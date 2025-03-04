"""Augmented Random Search (Mania et al., 2018).

Reference: https://arxiv.org/abs/1803.07055
"""

from collections.abc import Callable

import jax
import jax.numpy as jnp
import optax
from flax import struct

from ...types import Fitness, Population, Solution
from .base import DistributionBasedAlgorithm, Params, State, metrics_fn


@struct.dataclass
class State(State):
    mean: jax.Array
    std: float
    opt_state: optax.OptState
    z: jax.Array


@struct.dataclass
class Params(Params):
    std_init: float


class ARS(DistributionBasedAlgorithm):
    """Augmented Random Search (ARS)."""

    def __init__(
        self,
        population_size: int,
        solution: Solution,
        optimizer: optax.GradientTransformation = optax.adam(learning_rate=1e-3),
        metrics_fn: Callable = metrics_fn,
        **fitness_kwargs: bool | int | float,
    ):
        """Initialize ARS."""
        assert population_size % 2 == 0, "Population size must be even."
        super().__init__(population_size, solution, metrics_fn, **fitness_kwargs)

        self.elite_ratio = 0.5

        # Optimizer
        self.optimizer = optimizer

    @property
    def _default_params(self) -> Params:
        return Params(std_init=1.0)

    def _init(self, key: jax.Array, params: Params) -> State:
        state = State(
            mean=jnp.full((self.num_dims,), jnp.nan),
            std=params.std_init,
            opt_state=self.optimizer.init(jnp.zeros(self.num_dims)),
            z=jnp.zeros((self.population_size, self.num_dims)),
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
        return population, state.replace(z=z)

    def _tell(
        self,
        key: jax.Array,
        population: Population,
        fitness: Fitness,
        state: State,
        params: Params,
    ) -> State:
        # Get elites
        fitness_plus = fitness[: self.population_size // 2]
        fitness_minus = fitness[self.population_size // 2 :]
        elite_idx = jnp.argsort(jnp.minimum(fitness_plus, fitness_minus))[
            : self.num_elites
        ]

        # Compute elite fitness std
        fitness_elite = jnp.concatenate(
            [fitness_plus[elite_idx], fitness_minus[elite_idx]]
        )
        fitness_std = jnp.clip(jnp.std(fitness_elite), min=1e-8)

        # Compute grad
        z = state.z[: self.population_size // 2]
        delta = fitness_plus[elite_idx] - fitness_minus[elite_idx]
        grad = jnp.dot(z[elite_idx].T, delta) / (self.num_elites * fitness_std)

        # Update mean
        updates, opt_state = self.optimizer.update(grad, state.opt_state)
        mean = optax.apply_updates(state.mean, updates)

        return state.replace(mean=mean, opt_state=opt_state)
