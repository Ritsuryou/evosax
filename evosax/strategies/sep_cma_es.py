import chex
import jax
import jax.numpy as jnp
from flax import struct

from ..strategy import Strategy
from ..utils.eigen_decomp import diag_eigen_decomp


@struct.dataclass
class State:
    p_sigma: chex.Array
    p_c: chex.Array
    C: chex.Array
    D: chex.Array | None
    mean: chex.Array
    sigma: chex.Array
    sigma_scale: float
    weights: chex.Array
    weights_truncated: chex.Array
    best_member: chex.Array
    best_fitness: float = jnp.finfo(jnp.float32).max
    generation_counter: int = 0


@struct.dataclass
class Params:
    mu_eff: float
    c_1: float
    c_mu: float
    c_sigma: float
    d_sigma: float
    c_c: float
    chi_n: float
    c_m: float = 1.0
    sigma_init: float = 0.065
    init_min: float = 0.0
    init_max: float = 0.0
    clip_min: float = -jnp.finfo(jnp.float32).max
    clip_max: float = jnp.finfo(jnp.float32).max


def get_cma_elite_weights(
    population_size: int, elite_population_size: int
) -> tuple[chex.Array, chex.Array]:
    """Utility helper to create truncated elite weights for mean
    update and full weights for covariance update.
    """
    weights_prime = jnp.array(
        [
            jnp.log(elite_population_size + 1) - jnp.log(i + 1)
            for i in range(elite_population_size)
        ]
    )
    weights = weights_prime / jnp.sum(weights_prime)
    weights_truncated = jnp.zeros(population_size)
    weights_truncated = weights_truncated.at[:elite_population_size].set(weights)
    return weights, weights_truncated


class Sep_CMA_ES(Strategy):
    def __init__(
        self,
        population_size: int,
        solution: chex.ArrayTree | chex.Array | None = None,
        elite_ratio: float = 0.5,
        sigma_init: float = 1.0,
        mean_decay: float = 0.0,
        **fitness_kwargs: bool | int | float,
    ):
        """Separable CMA-ES (e.g. Ros & Hansen, 2008)
        Reference: https://hal.inria.fr/inria-00287367/document
        Inspired by: github.com/CyberAgentAILab/cmaes/blob/main/cmaes/_sepcma.py
        """
        super().__init__(
            population_size,
            solution,
            mean_decay,
            **fitness_kwargs,
        )
        assert 0 <= elite_ratio <= 1
        self.elite_ratio = elite_ratio
        self.elite_population_size = max(
            1, int(self.population_size * self.elite_ratio)
        )
        self.strategy_name = "Sep_CMA_ES"

        # Set core kwargs params
        self.sigma_init = sigma_init

        # Robustness for int32 - squaring in hyperparameter calculations
        self.max_dims_sq = jnp.minimum(self.num_dims, 40000)

    @property
    def params_strategy(self) -> Params:
        """Return default parameters of evolution strategy."""
        # Temporarily create elite weights for rest of parameters
        weights, _ = get_cma_elite_weights(
            self.population_size, self.elite_population_size
        )
        mu_eff = 1 / jnp.sum(weights**2)

        # lrates for rank-one and rank-μ C updates
        alpha_cov = 2
        c_1 = alpha_cov / ((self.max_dims_sq + 1.3) ** 2 + mu_eff)
        c_mu_full = 2 / mu_eff / ((self.max_dims_sq + jnp.sqrt(2)) ** 2) + (
            1 - 1 / mu_eff
        ) * jnp.minimum(1, (2 * mu_eff - 1) / ((self.max_dims_sq + 2) ** 2 + mu_eff))
        c_mu = (self.num_dims + 2) / 3 * c_mu_full

        # lrate for cumulation of step-size control and rank-one update
        c_sigma = (mu_eff + 2) / (self.num_dims + mu_eff + 3)
        d_sigma = (
            1
            + 2 * jnp.maximum(0, jnp.sqrt((mu_eff - 1) / (self.num_dims + 1)) - 1)
            + c_sigma
        )
        c_c = 4 / (self.num_dims + 4)
        chi_n = jnp.sqrt(self.num_dims) * (
            1.0 - (1.0 / (4.0 * self.num_dims)) + 1.0 / (21.0 * (self.max_dims_sq**2))
        )
        params = Params(
            mu_eff=mu_eff,
            c_1=c_1,
            c_mu=c_mu,
            c_sigma=c_sigma,
            d_sigma=d_sigma,
            c_c=c_c,
            chi_n=chi_n,
            sigma_init=self.sigma_init,
        )
        return params

    def init_strategy(self, key: jax.Array, params: Params) -> State:
        """`init` the evolution strategy."""
        # Population weightings - store in state
        weights, weights_truncated = get_cma_elite_weights(
            self.population_size, self.elite_population_size
        )
        # Initialize evolution paths & covariance matrix
        initialization = jax.random.uniform(
            key,
            (self.num_dims,),
            minval=params.init_min,
            maxval=params.init_max,
        )
        state = State(
            p_sigma=jnp.zeros(self.num_dims),
            p_c=jnp.zeros(self.num_dims),
            sigma_scale=params.sigma_init,
            sigma=jnp.ones(self.num_dims) * params.sigma_init,
            mean=initialization,
            C=jnp.ones(self.num_dims),
            D=diag_eigen_decomp(jnp.ones(self.num_dims), None),
            weights=weights,
            weights_truncated=weights_truncated,
            best_member=initialization,
        )
        return state

    def ask_strategy(
        self, key: jax.Array, state: State, params: Params
    ) -> tuple[chex.Array, State]:
        """`ask` for new parameter candidates to evaluate next."""
        x = sample(
            key,
            state.mean,
            state.sigma_scale,
            state.D,
            self.num_dims,
            self.population_size,
        )
        return x, state

    def tell_strategy(
        self,
        x: chex.Array,
        fitness: chex.Array,
        state: State,
        params: Params,
    ) -> State:
        """`tell` performance data for strategy state update."""
        # Sort new results, extract elite, store best performer
        concat_p_f = jnp.hstack([jnp.expand_dims(fitness, 1), x])
        sorted_solutions = concat_p_f[concat_p_f[:, 0].argsort()]
        # Update mean, isotropic/anisotropic paths, covariance, stepsize
        y_k, y_w, mean = update_mean(
            state.mean,
            state.sigma,
            sorted_solutions,
            params.c_m,
            state.weights_truncated,
        )

        p_sigma, D = update_p_sigma(
            state.C, state.D, state.p_sigma, y_w, params.c_sigma, params.mu_eff
        )

        p_c, norm_p_sigma, h_sigma = update_p_c(
            mean,
            p_sigma,
            state.p_c,
            state.generation_counter + 1,
            y_w,
            params.c_sigma,
            params.c_c,
            params.chi_n,
            params.mu_eff,
        )

        C = update_covariance(
            p_c,
            state.C,
            y_k,
            h_sigma,
            state.weights_truncated,
            params.c_c,
            params.c_1,
            params.c_mu,
        )
        sigma_scale = update_sigma(
            state.sigma_scale,
            norm_p_sigma,
            params.c_sigma,
            params.d_sigma,
            params.chi_n,
        )
        sigma = sigma_scale * D
        return state.replace(
            mean=mean,
            p_sigma=p_sigma,
            C=C,
            D=D,
            p_c=p_c,
            sigma_scale=sigma_scale,
            sigma=sigma,
        )


def update_mean(
    mean: chex.Array,
    sigma: float,
    sorted_solutions: chex.Array,
    c_m: float,
    weights_truncated: chex.Array,
) -> tuple[chex.Array, chex.Array, chex.Array]:
    """Update mean of strategy."""
    x_k = sorted_solutions[:, 1:]  # ~ N(m, σ^2 C)
    y_k = (x_k - mean) / sigma  # ~ N(0, C)
    y_w = jnp.sum(y_k.T * weights_truncated, axis=1)
    mean += c_m * sigma * y_w
    return y_k, y_w, mean


def update_p_sigma(
    C: chex.Array,
    D: chex.Array,
    p_sigma: chex.Array,
    y_w: chex.Array,
    c_sigma: float,
    mu_eff: float,
) -> tuple[chex.Array, None]:
    """Update evolution path for covariance matrix."""
    D = diag_eigen_decomp(C, D)
    p_sigma_new = (1 - c_sigma) * p_sigma + jnp.sqrt(
        c_sigma * (2 - c_sigma) * mu_eff
    ) * (y_w / D)
    return p_sigma_new, D


def update_p_c(
    mean: chex.Array,
    p_sigma: chex.Array,
    p_c: chex.Array,
    generation_counter: int,
    y_w: chex.Array,
    c_sigma: float,
    c_c: float,
    chi_n: float,
    mu_eff: float,
) -> tuple[chex.Array, float, float]:
    """Update evolution path for sigma/stepsize."""
    norm_p_sigma = jnp.linalg.norm(p_sigma)
    h_sigma_cond_left = norm_p_sigma / jnp.sqrt(
        1 - (1 - c_sigma) ** (2 * (generation_counter))
    )
    h_sigma_cond_right = (1.4 + 2 / (mean.shape[0] + 1)) * chi_n
    h_sigma = 1.0 * (h_sigma_cond_left < h_sigma_cond_right)
    p_c_new = (1 - c_c) * p_c + h_sigma * jnp.sqrt(c_c * (2 - c_c) * mu_eff) * y_w
    return p_c_new, norm_p_sigma, h_sigma


def update_covariance(
    p_c: chex.Array,
    C: chex.Array,
    y_k: chex.Array,
    h_sigma: float,
    weights_truncated: chex.Array,
    c_c: float,
    c_1: float,
    c_mu: float,
) -> chex.Array:
    """Update cov. matrix estimator using rank 1 + μ updates."""
    delta_h_sigma = (1 - h_sigma) * c_c * (2 - c_c)
    rank_one = p_c**2
    rank_mu = jnp.einsum("i,ij->j", weights_truncated, y_k**2)
    C = (
        (1 + c_1 * delta_h_sigma - c_1 - c_mu * jnp.sum(weights_truncated)) * C
        + c_1 * rank_one
        + c_mu * rank_mu
    )
    return C


def update_sigma(
    sigma: float,
    norm_p_sigma: float,
    c_sigma: float,
    d_sigma: float,
    chi_n: float,
) -> float:
    """Update stepsize sigma."""
    sigma_new = sigma * jnp.exp((c_sigma / d_sigma) * (norm_p_sigma / chi_n - 1))
    return sigma_new


def sample(
    key: jax.Array,
    mean: chex.Array,
    sigma_scale: float,
    D: chex.Array,
    n_dim: int,
    pop_size: int,
) -> chex.Array:
    """Jittable Gaussian Sample Helper."""
    z = jax.random.normal(key, (n_dim, pop_size))  # ~ N(0, I)
    y = jnp.diag(D).dot(
        z
    )  # ~ N(0, C)  TODO: check if this is correct (discrepency between C and D
    y = jnp.swapaxes(y, 1, 0)
    x = mean + sigma_scale * y  # ~ N(m, σ^2 C)
    return x
