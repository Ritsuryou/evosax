"""Policy Gradients with Parameter-Based Exploration (Sehnke et al., 2010).

Reference: https://link.springer.com/chapter/10.1007/978-3-540-87536-9_40
"""

from collections.abc import Callable

import jax
import jax.numpy as jnp
import optax
from flax import struct

from ...core.optimizer import clipup
from ...types import Fitness, Population, Solution
from .base import DistributionBasedAlgorithm, Params, State, metrics_fn


@struct.dataclass
class State(State):
    mean: jax.Array
    std: jax.Array
    opt_state: optax.OptState


@struct.dataclass
class Params(Params):
    std_init: float
    std_decay: float
    std_limit: float
    std_lrate: float  # Learning rate for std
    std_max_change: float  # Clip adaptive std to 20%


class PGPE(DistributionBasedAlgorithm):
    """Policy Gradients with Parameter-Based Exploration (PGPE)."""

    def __init__(
        self,
        population_size: int,
        solution: Solution,
        optimizer: optax.GradientTransformation = clipup(
            learning_rate=0.05, max_velocity=0.1
        ),
        metrics_fn: Callable = metrics_fn,
        **fitness_kwargs: bool | int | float,
    ):
        """Initialize PGPE."""
        assert population_size % 2 == 0, "Population size must be even."
        super().__init__(population_size, solution, metrics_fn, **fitness_kwargs)

        # Optimizer
        self.optimizer = optimizer

    @property
    def _default_params(self) -> Params:
        return Params(
            std_init=1.0,
            std_decay=1.0,
            std_limit=0.0,
            std_lrate=0.1,
            std_max_change=0.2,
        )

    def _init(self, key: jax.Array, params: Params) -> State:
        state = State(
            mean=jnp.full((self.num_dims,), jnp.nan),
            std=jnp.full((self.num_dims,), params.std_init),
            opt_state=self.optimizer.init(jnp.zeros(self.num_dims)),
            best_solution=jnp.full((self.num_dims,), jnp.nan),
            best_fitness=jnp.inf,
            generation_counter=0,
        )
        return state

    def _ask(
        self,
        key: jax.Array,
        state: State,
        params: Params,
    ) -> tuple[Population, State]:
        # Antithetic sampling
        z_plus = jax.random.normal(key, (self.population_size // 2, self.num_dims))
        z = jnp.concatenate([z_plus, -z_plus])

        population = state.mean + state.std * z
        return population, state

    def _tell(
        self,
        key: jax.Array,
        population: Population,
        fitness: Fitness,
        state: State,
        params: Params,
    ) -> State:
        z_scaled = population[: self.population_size // 2] - state.mean
        fitness_plus = fitness[: self.population_size // 2]
        fitness_minus = fitness[self.population_size // 2 :]

        # Compute grad for mean
        # grad_mean = jnp.mean(
        #     0.5 * (fitness_plus - fitness_minus)[:, None] * z_scaled, axis=0
        # )
        grad_mean = (
            jnp.dot(fitness_plus - fitness_minus, z_scaled) / self.population_size
        )  # equivalent to the above

        # Compute grad for std
        baseline = jnp.mean(fitness)
        # grad_std = jnp.mean(
        #     (0.5 * (fitness_plus + fitness_minus) - baseline)
        #     * (z_scaled**2 - state.std**2)
        #     / state.std,
        #     axis=0,
        # )
        grad_std = (
            jnp.dot(
                fitness_plus + fitness_minus - 2 * baseline,
                (z_scaled**2 - state.std**2) / state.std,
            )
            / self.population_size
        )  # equivalent to the above

        # Update mean
        updates, opt_state = self.optimizer.update(grad_mean, state.opt_state)
        mean = optax.apply_updates(state.mean, updates)

        # Update std
        std_max_change = params.std_max_change * state.std
        std_min = state.std - std_max_change
        std_max = state.std + std_max_change

        std = jnp.clip(
            state.std - params.std_lrate * grad_std,
            min=std_min,
            max=std_max,
        )
        std = jnp.clip(std * params.std_decay, min=params.std_limit)

        return state.replace(mean=mean, std=std, opt_state=opt_state)
