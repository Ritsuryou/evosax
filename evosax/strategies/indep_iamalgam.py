import chex
import jax
import jax.numpy as jnp
from flax import struct

from ..core import exp_decay
from ..strategy import Strategy
from .full_iamalgam import (
    adaptive_variance_scaling,
    anticipated_mean_shift,
    update_mean_amalgam,
)


@struct.dataclass
class State:
    mean: chex.Array
    mean_shift: chex.Array
    C: chex.Array
    nis_counter: int
    c_mult: float
    sigma: float
    best_member: chex.Array
    best_fitness: float = jnp.finfo(jnp.float32).max
    generation_counter: int = 0


@struct.dataclass
class Params:
    eta_sigma: float
    eta_shift: float
    eta_avs_inc: float = 1.0 / 0.9
    eta_avs_dec: float = 0.9
    nis_max_gens: int = 50
    delta_ams: float = 2.0
    theta_sdr: float = 1.0
    c_mult_init: float = 1.0
    sigma_init: float = 0.0
    sigma_decay: float = 0.999
    sigma_limit: float = 0.0
    init_min: float = 0.0
    init_max: float = 0.0
    clip_min: float = -jnp.finfo(jnp.float32).max
    clip_max: float = jnp.finfo(jnp.float32).max


class Indep_iAMaLGaM(Strategy):
    def __init__(
        self,
        population_size: int,
        solution: chex.ArrayTree | chex.Array | None = None,
        elite_ratio: float = 0.35,
        sigma_init: float = 0.0,
        sigma_decay: float = 0.99,
        sigma_limit: float = 0.0,
        mean_decay: float = 0.0,
        **fitness_kwargs: bool | int | float,
    ):
        """(Iterative) AMaLGaM (Bosman et al., 2013) - Diagonal Covariance
        Reference: https://tinyurl.com/y9fcccx2
        """
        super().__init__(population_size, solution, mean_decay, **fitness_kwargs)
        assert 0 <= elite_ratio <= 1
        self.elite_ratio = elite_ratio
        self.elite_population_size = max(
            1, int(self.population_size * self.elite_ratio)
        )
        alpha_ams = (
            0.5
            * self.elite_ratio
            * self.population_size
            / (self.population_size - self.elite_population_size)
        )
        self.ams_population_size = int(alpha_ams * (self.population_size - 1))
        self.strategy_name = "Indep_iAMaLGaM"

        # Set core kwargs params
        self.sigma_init = sigma_init
        self.sigma_decay = sigma_decay
        self.sigma_limit = sigma_limit

    @property
    def params_strategy(self) -> Params:
        """Return default parameters of evolution strategy."""
        a_0_sigma, a_1_sigma, a_2_sigma = -1.1, 1.2, 1.6
        a_0_shift, a_1_shift, a_2_shift = -1.2, 0.31, 0.5
        eta_sigma = 1 - jnp.exp(
            a_0_sigma
            * self.elite_population_size**a_1_sigma
            / (self.num_dims**a_2_sigma)
        )
        eta_shift = 1 - jnp.exp(
            a_0_shift
            * self.elite_population_size**a_1_shift
            / (self.num_dims**a_2_shift)
        )

        return Params(
            eta_sigma=eta_sigma,
            eta_shift=eta_shift,
            sigma_init=self.sigma_init,
            sigma_decay=self.sigma_decay,
            sigma_limit=self.sigma_limit,
        )

    def init_strategy(self, key: jax.Array, params: Params) -> State:
        """`init` the evolution strategy."""
        # Initialize evolution paths & covariance matrix
        initialization = jax.random.uniform(
            key,
            (self.num_dims,),
            minval=params.init_min,
            maxval=params.init_max,
        )
        state = State(
            mean=initialization,
            mean_shift=jnp.zeros(self.num_dims),
            C=jnp.ones(self.num_dims),
            sigma=params.sigma_init,
            nis_counter=0,
            c_mult=params.c_mult_init,
            best_member=initialization,
        )
        return state

    def ask_strategy(
        self, key: jax.Array, state: State, params: Params
    ) -> tuple[chex.Array, State]:
        """`ask` for new parameter candidates to evaluate next."""
        key_sample, key_ams = jax.random.split(key)
        x = sample(key_sample, state.mean, state.C, state.sigma, self.population_size)
        x_ams = anticipated_mean_shift(
            key_ams,
            x,
            self.ams_population_size,
            params.delta_ams,
            state.c_mult,
            state.mean_shift,
        )
        return x_ams, state

    def tell_strategy(
        self,
        x: chex.Array,
        fitness: chex.Array,
        state: State,
        params: Params,
    ) -> State:
        """`tell` performance data for strategy state update."""
        # Sort new results, extract elite
        idx = jnp.argsort(fitness)[0 : self.elite_population_size]
        fitness_elite = fitness[idx]
        members_elite = x[idx]

        # If there has been a fitness improvement -> Run AVS based on SDR
        improvements = fitness_elite < state.best_fitness
        any_improvement = jnp.sum(improvements) > 0
        sdr = standard_deviation_ratio(improvements, members_elite, state.mean, state.C)
        c_mult, nis_counter = adaptive_variance_scaling(
            any_improvement,
            sdr,
            state.c_mult,
            state.nis_counter,
            params.theta_sdr,
            params.eta_avs_inc,
            params.eta_avs_dec,
            params.nis_max_gens,
        )

        # Update mean and covariance estimates - difference full vs. indep
        mean, mean_shift = update_mean_amalgam(
            members_elite,
            state.mean,
            state.mean_shift,
            params.eta_shift,
        )
        C = update_cov_amalgam(members_elite, state.C, mean, params.eta_sigma)

        # Decay isotropic part of Gaussian search distribution
        sigma = exp_decay(state.sigma, params.sigma_decay, params.sigma_limit)
        return state.replace(
            c_mult=c_mult,
            nis_counter=nis_counter,
            mean=mean,
            mean_shift=mean_shift,
            C=C,
            sigma=sigma,
        )


def sample(
    key: jax.Array,
    mean: chex.Array,
    C: chex.Array,
    sigma: float,
    population_size: int,
) -> chex.Array:
    """Jittable Gaussian Sample Helper."""
    sigmas = jnp.sqrt(C) + sigma
    z = jax.random.normal(key, (mean.shape[0], population_size))  # ~ N(0, I)
    y = jnp.diag(sigmas).dot(z)  # ~ N(0, C)
    y = jnp.swapaxes(y, 1, 0)
    x = mean + y  # ~ N(m, σ^2 C)
    return x


def standard_deviation_ratio(
    improvements: chex.Array,
    members_elite: chex.Array,
    mean: chex.Array,
    C: chex.Array,
) -> float:
    """SDR - relate dist. of improvements to mean in param space."""
    # Compute avg. member for candidates that improve fitness -> SDR
    x_avg_imp = jnp.sum(improvements[:, jnp.newaxis] * members_elite, axis=0) / jnp.sum(
        improvements
    )
    conditioned_diff = (x_avg_imp - mean) / C
    sdr = jnp.max(jnp.abs(conditioned_diff))
    return sdr


def update_cov_amalgam(
    members_elite: chex.Array,
    C: chex.Array,
    mean: chex.Array,
    eta_sigma: float,
) -> chex.Array:
    """Iterative update of mean and mean shift based on elite and history."""
    S_bar = members_elite - mean
    # Univariate update to standard deviations
    new_C = (1 - eta_sigma) * C + eta_sigma * jnp.sum(
        S_bar**2, axis=0
    ) / members_elite.shape[0]
    return new_C
