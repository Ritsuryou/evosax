import chex
import jax
import jax.numpy as jnp
from flax import struct

from ..strategy import Strategy


@struct.dataclass
class State:
    archive: chex.Array
    fitness: chex.Array
    copy_id: chex.Array
    best_member: chex.Array
    best_fitness: float = jnp.finfo(jnp.float32).max
    generation_counter: int = 0


@struct.dataclass
class Params:
    noise_scale: float = 0.1
    truncation_selection: float = 0.2
    init_min: float = 0.0
    init_max: float = 0.0
    clip_min: float = -jnp.finfo(jnp.float32).max
    clip_max: float = jnp.finfo(jnp.float32).max


class PBT(Strategy):
    def __init__(
        self,
        population_size: int,
        solution: chex.ArrayTree | chex.Array | None = None,
        **fitness_kwargs: bool | int | float,
    ):
        """Synchronous Population-Based Training (Jaderberg et al., 2017)
        Reference: https://arxiv.org/abs/1711.09846
        """
        super().__init__(population_size, solution, **fitness_kwargs)
        self.strategy_name = "PBT"

    @property
    def params_strategy(self) -> Params:
        """Return default parameters of evolution strategy."""
        return Params()

    def init_strategy(self, key: jax.Array, params: Params) -> State:
        """`init` the differential evolution strategy."""
        initialization = jax.random.uniform(
            key,
            (self.population_size, self.num_dims),
            minval=params.init_min,
            maxval=params.init_max,
        )
        state = State(
            archive=initialization,
            fitness=jnp.zeros(self.population_size) - 20e10,
            copy_id=jnp.zeros(self.population_size, dtype=jnp.int32),
            best_member=jnp.zeros(self.num_dims),
        )
        return state

    def ask_strategy(
        self, key: jax.Array, state: State, params: Params
    ) -> tuple[chex.Array, State]:
        """`ask` for new proposed candidates to evaluate next.
        Perform explore-exploit step.
        1) Check exploit criterion (e.g. in top 20% of performer).
        2) If not exploit: Copy hyperparams from id and explore/perturb around.
        3) Return new hyperparameters and copy_id (same if exploit)
        """
        keys = jax.random.split(key, self.population_size)
        member_ids = jnp.arange(self.population_size)
        exploit_bool, copy_id, hyperparams = jax.vmap(
            single_member_exploit, in_axes=(0, None, None, None)
        )(member_ids, state.archive, state.fitness, params)
        hyperparams = jax.vmap(single_member_explore, in_axes=(0, 0, 0, None))(
            keys, exploit_bool, hyperparams, params
        )
        return hyperparams, state.replace(copy_id=copy_id)

    def tell_strategy(
        self,
        x: chex.Array,
        fitness: chex.Array,
        state: State,
        params: Params,
    ) -> State:
        """`tell` update to ES state. - Only copy if improved performance."""
        replace = fitness >= state.fitness
        archive = (
            jnp.expand_dims(replace, 1) * x
            + (1 - jnp.expand_dims(replace, 1)) * state.archive
        )
        fitness = replace * fitness + (1 - replace) * state.fitness
        return state.replace(archive=archive, fitness=fitness)


def single_member_exploit(
    member_id: int,
    archive: chex.Array,
    fitness: chex.Array,
    params: Params,
) -> tuple[bool, int, chex.Array]:
    """Get the top and bottom performers."""
    best_id = jnp.argmax(fitness)
    exploit_bool = member_id != best_id  # Copy if worker not best
    copy_id = jax.lax.select(exploit_bool, best_id, member_id)
    hyperparams_copy = archive[copy_id]
    return exploit_bool, copy_id, hyperparams_copy


def single_member_explore(
    key: jax.Array,
    exploit_bool: int,
    hyperparams: chex.Array,
    params: Params,
) -> chex.Array:
    """Perform multiplicative noise exploration."""
    explore_noise = jax.random.normal(key, hyperparams.shape) * params.noise_scale
    hyperparams_explore = jax.lax.select(
        exploit_bool, hyperparams + explore_noise, hyperparams
    )
    return hyperparams_explore
