import chex
import jax
import jax.numpy as jnp
from flax import struct

from ..strategy import Strategy


@struct.dataclass
class EvoState:
    mean: chex.Array
    best_member: chex.Array
    best_fitness: float = jnp.finfo(jnp.float32).max
    generation_counter: int = 0


@struct.dataclass
class EvoParams:
    init_min: float = 0.0
    init_max: float = 0.0
    range_min: float = 0.0
    range_max: float = 1.0
    clip_min: float = -jnp.finfo(jnp.float32).max
    clip_max: float = jnp.finfo(jnp.float32).max


class RandomSearch(Strategy):
    def __init__(
        self,
        population_size: int,
        pholder_params: chex.ArrayTree | chex.Array | None = None,
        **fitness_kwargs: bool | int | float,
    ):
        """Simple Random Search Baseline"""
        super().__init__(population_size, pholder_params, **fitness_kwargs)
        self.strategy_name = "RandomSearch"

    @property
    def params_strategy(self) -> EvoParams:
        """Return default parameters of evolution strategy."""
        return EvoParams()

    def init_strategy(self, key: jax.Array, params: EvoParams) -> EvoState:
        """`init` the differential evolution strategy."""
        initialization = jax.random.uniform(
            key,
            (self.num_dims,),
            minval=params.init_min,
            maxval=params.init_max,
        )
        state = EvoState(
            mean=initialization,
            best_member=initialization,
        )
        return state

    def ask_strategy(
        self, key: jax.Array, state: EvoState, params: EvoParams
    ) -> tuple[chex.Array, EvoState]:
        """`ask` for new proposed candidates to evaluate next."""
        x = jax.random.uniform(
            key,
            (self.population_size, self.num_dims),
            minval=params.range_min,
            maxval=params.range_max,
        )
        return x, state

    def tell_strategy(
        self,
        x: chex.Array,
        fitness: chex.Array,
        state: EvoState,
        params: EvoParams,
    ) -> EvoState:
        """`tell` update to ES state."""
        idx = jnp.argsort(fitness)
        fitness = fitness[idx]
        x = x[idx]
        # Set mean to best member seen so far
        improved = fitness[0] < state.best_fitness
        best_mean = jax.lax.select(improved, x[0], state.best_member)
        return state.replace(mean=best_mean)
