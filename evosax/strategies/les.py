import pkgutil

import jax
import jax.numpy as jnp
from flax import struct

from ..learned_eo.les_tools import (
    AttentionWeights,
    EvolutionPath,
    EvoPathMLP,
    FitnessFeatures,
    load_pkl_object,
    tanh_timestamp,
)
from ..strategy import Strategy
from ..types import ArrayTree, Fitness, Population, Solution


@struct.dataclass
class State:
    mean: jax.Array
    sigma: jax.Array
    path_c: jax.Array
    path_sigma: jax.Array
    best_member: jax.Array
    best_fitness: float = jnp.finfo(jnp.float32).max
    generation_counter: int = 0


@struct.dataclass
class Params:
    net_params: ArrayTree
    sigma_init: float = 0.1
    init_min: float = -5.0
    init_max: float = 5.0
    clip_min: float = -jnp.finfo(jnp.float32).max
    clip_max: float = jnp.finfo(jnp.float32).max


class LES(Strategy):
    """Population-Invariant Learned Evolution Strategy (Lange et al., 2023)."""

    # NOTE: This is an independent reimplementation which does not use the same
    # meta-trained checkpoint used to generate the results in the paper. It
    # has been independently meta-trained & tested on a handful of Brax tasks.
    # The results may therefore differ from the ones shown in the paper.
    def __init__(
        self,
        population_size: int,
        solution: Solution,
        net_params: ArrayTree | None = None,
        net_ckpt_path: str | None = None,
        sigma_init: float = 0.1,
        mean_decay: float = 0.0,
        **fitness_kwargs: bool | int | float,
    ):
        super().__init__(
            population_size,
            solution,
            mean_decay,
            **fitness_kwargs,
        )
        self.strategy_name = "LES"
        self.evopath = EvolutionPath(
            num_dims=self.num_dims, timescales=jnp.array([0.1, 0.5, 0.9])
        )
        self.weight_layer = AttentionWeights(8)
        self.lrate_layer = EvoPathMLP(8)
        self.fitness_features = FitnessFeatures(centered_rank=True, z_score=True)
        self.sigma_init = sigma_init

        # Set net params provided at instantiation
        if net_params is not None:
            self.les_net_params = net_params

        # Load network weights from checkpoint
        if net_ckpt_path is not None:
            self.les_net_params = load_pkl_object(net_ckpt_path)
            print(f"Loaded LES model from ckpt: {net_ckpt_path}")

        if net_params is None and net_ckpt_path is None:
            ckpt_fname = "2023_10_les_v2.pkl"
            data = pkgutil.get_data(__name__, f"ckpt/les/{ckpt_fname}")
            self.les_net_params = load_pkl_object(data, pkg_load=True)
            print(f"Loaded pretrained LES model from ckpt: {ckpt_fname}")

    @property
    def params_strategy(self) -> Params:
        """Return default parameters of evolution strategy."""
        return Params(net_params=self.les_net_params, sigma_init=self.sigma_init)

    def init_strategy(self, key: jax.Array, params: Params) -> State:
        """`init` the evolution strategy."""
        init_mean = jax.random.uniform(
            key,
            (self.num_dims,),
            minval=params.init_min,
            maxval=params.init_max,
        )
        init_sigma = params.sigma_init * jnp.ones(self.num_dims)
        init_path_c = self.evopath.init()
        init_path_sigma = self.evopath.init()
        return State(
            mean=init_mean,
            sigma=init_sigma,
            path_c=init_path_c,
            path_sigma=init_path_sigma,
            best_member=init_mean,
        )

    def ask_strategy(
        self, key: jax.Array, state: State, params: Params
    ) -> tuple[jax.Array, State]:
        """`ask` for new parameter candidates to evaluate next."""
        noise = jax.random.normal(key, (self.population_size, self.num_dims))
        x = state.mean + noise * state.sigma.reshape(1, self.num_dims)
        x = jnp.clip(x, params.clip_min, params.clip_max)
        return x, state

    def tell_strategy(
        self,
        x: Population,
        fitness: Fitness,
        state: State,
        params: Params,
    ) -> State:
        """`tell` performance data for strategy state update."""
        fit_re = self.fitness_features.apply(x, fitness, state.best_fitness)
        time_embed = tanh_timestamp(state.generation_counter)
        weights = self.weight_layer.apply(params.net_params["recomb_weights"], fit_re)
        weight_diff = (weights * (x - state.mean)).sum(axis=0)
        weight_noise = (weights * (x - state.mean) / state.sigma).sum(axis=0)
        path_c = self.evopath.update(state.path_c, weight_diff)
        path_sigma = self.evopath.update(state.path_sigma, weight_noise)
        lrates_mean, lrates_sigma = self.lrate_layer.apply(
            params.net_params["lrate_modulation"],
            path_c,
            path_sigma,
            time_embed,
        )
        weighted_mean = (weights * x).sum(axis=0)
        weighted_sigma = jnp.sqrt((weights * (x - state.mean) ** 2).sum(axis=0) + 1e-10)
        mean_change = lrates_mean * (weighted_mean - state.mean)
        sigma_change = lrates_sigma * (weighted_sigma - state.sigma)
        mean = state.mean + mean_change
        sigma = state.sigma + sigma_change
        mean = jnp.clip(mean, params.clip_min, params.clip_max)
        sigma = jnp.clip(sigma, 0, params.clip_max)
        return state.replace(
            mean=mean,
            sigma=sigma,
            path_c=path_c,
            path_sigma=path_sigma,
        )
