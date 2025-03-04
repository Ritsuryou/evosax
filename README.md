# `evosax`: Evolution Strategies in JAX 🦎

[![Pyversions](https://img.shields.io/pypi/pyversions/evosax.svg?style=flat-square)](https://pypi.python.org/pypi/evosax) [![PyPI version](https://badge.fury.io/py/evosax.svg)](https://badge.fury.io/py/evosax)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/RobertTLange/evosax/branch/main/graph/badge.svg?token=5FUSX35KWO)](https://codecov.io/gh/RobertTLange/evosax)
[![Paper](http://img.shields.io/badge/paper-arxiv.2212.04180-B31B1B.svg)](http://arxiv.org/abs/2212.04180)
<a href="https://github.com/RobertTLange/evosax/blob/main/docs/logo.png?raw=true"><img src="https://github.com/RobertTLange/evosax/blob/main/docs/logo.png?raw=true" width="170" align="right" /></a>

Tired of having to handle asynchronous processes for neuroevolution? Do you want to leverage massive vectorization and high-throughput accelerators for evolution strategies (ES)? `evosax` allows you to leverage JAX, XLA compilation and auto-vectorization/parallelization to scale ES to your favorite accelerators. The API is based on the classical `ask`, `evaluate`, `tell` cycle of ES. Both `ask` and `tell` calls are compatible with `jit`, `vmap`/`pmap` and `lax.scan`. It includes a vast set of both classic (e.g. CMA-ES, Differential Evolution, etc.) and modern neuroevolution (e.g. OpenAI-ES, Augmented RS, etc.) strategies. You can get started here 👉 [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/00_getting_started.ipynb)

## Basic `evosax` API Usage 🍲

```python
import jax
from evosax import CMA_ES

# Instantiate the search strategy
key = jax.random.key(0)
strategy = CMA_ES(population_size=20, num_dims=2, elite_ratio=0.5)
params = strategy.default_params
state = strategy.init(key, params)

# Run ask-eval-tell loop - NOTE: By default minimization!
for t in range(num_generations):
    key, key_ask, key_eval = jax.random.split(key, 3)
    x, state = strategy.ask(key_ask, state, params)
    fitness = ...  # Your population evaluation fct 
    state = strategy.tell(x, fitness, state, params)

# Get best overall population member & its fitness
state.best_member, state.best_fitness
```

## Implemented Evolution Strategies 🦎

| Strategy                    | Reference                                                                                                                                                | Import                                                                                                   | Example |
|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------| --- |
| OpenAI-ES                   | [Salimans et al. (2017)](https://arxiv.org/pdf/1703.03864.pdf)                                                                                           | [`OpenES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/open_es.py)                | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/03_cnn_mnist.ipynb)
| PGPE                        | [Sehnke et al. (2010)](https://citeseerx.ist.psu.edu/viewdoc/download;jsessionid=A64D1AE8313A364B814998E9E245B40A?doi=10.1.1.180.7104&rep=rep1&type=pdf) | [`PGPE`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/pgpe.py)                     | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/02_mlp_control.ipynb)
| ARS                         | [Mania et al. (2018)](https://arxiv.org/pdf/1803.07055.pdf)                                                                                              | [`ARS`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/ars.py)                       | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/00_getting_started.ipynb)
| ESMC                        | [Merchant et al. (2021)](https://proceedings.mlr.press/v139/merchant21a.html)                                                                            | [`ESMC`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/esmc.py)                     | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| Persistent ES               | [Vicol et al. (2021)](http://proceedings.mlr.press/v139/vicol21a.html)                                                                                   | [`PES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/persistent_es.py)    | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/07_persistent_es.ipynb)
| Noise-Reuse ES              | [Li et al. (2023)](https://arxiv.org/pdf/2304.12180.pdf)                                                                                                 | [`NoiseReuseES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/noise_reuse_es.py)   | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/07_persistent_es.ipynb)
| xNES                        | [Wierstra et al. (2014)](https://www.jmlr.org/papers/volume15/wierstra14a/wierstra14a.pdf)                                                               | [`XNES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/xnes.py)                     | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| SNES                        | [Wierstra et al. (2014)](https://www.jmlr.org/papers/volume15/wierstra14a/wierstra14a.pdf)                                                               | [`SNES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/sxnes.py)                    | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| CR-FM-NES                   | [Nomura & Ono (2022)](https://arxiv.org/abs/2201.11422)                                                                                                  | [`CR_FM_NES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/cr_fm_nes.py)           | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| Guided ES                   | [Maheswaranathan et al. (2018)](https://arxiv.org/abs/1806.10230)                                                                                        | [`GuidedES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/guided_es.py)            | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| ASEBO                       | [Choromanski et al. (2019)](https://arxiv.org/abs/1903.04268)                                                                                            | [`ASEBO`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/asebo.py)                   | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| CMA-ES                      | [Hansen & Ostermeier (2001)](http://www.cmap.polytechnique.fr/~nikolaus.hansen/cmaartic.pdf)                                                             | [`CMA_ES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/cma_es.py)                 | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| Sep-CMA-ES                  | [Ros & Hansen (2008)](https://hal.inria.fr/inria-00287367/document)                                                                                      | [`Sep_CMA_ES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/sep_cma_es.py)         | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| BIPOP-CMA-ES                | [Hansen (2009)](https://hal.inria.fr/inria-00382093/document)                                                                                            | [`BIPOP_CMA_ES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/bipop_cma_es.py)     | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/06_restart_es.ipynb)
| IPOP-CMA-ES                 | [Auer & Hansen (2005)](http://www.cmap.polytechnique.fr/~nikolaus.hansen/cec2005ipopcmaes.pdf)                                                           | [`IPOP_CMA_ES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/ipop_cma_es.py)       | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/06_restart_es.ipynb)
| iAMaLGaM-Full               | [Bosman et al. (2013)](https://tinyurl.com/y9fcccx2)                                                                                                     | [`iAMaLGaM_Full`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/iamalgam_full.py)   |[![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| iAMaLGaM-Univariate         | [Bosman et al. (2013)](https://tinyurl.com/y9fcccx2)                                                                                                     | [`iAMaLGaM_Univariate`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/iAMaLGaM_Univariate.py) | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| MA-ES                       | [Bayer & Sendhoff (2017)](https://www.honda-ri.de/pubs/pdf/3376.pdf)                                                                                     | [`MA_ES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/ma_es.py)                   | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| LM-MA-ES                    | [Loshchilov et al. (2017)](https://arxiv.org/pdf/1705.06693.pdf)                                                                                         | [`LM_MA_ES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/lm_ma_es.py)             | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| Rm_ES                        | [Li & Zhang (2017)](https://ieeexplore.ieee.org/document/8080257)                                                                                        | [`Rm_ES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/rm_es.py)                    | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| Simple Genetic              | [Such et al. (2017)](https://arxiv.org/abs/1712.06567)                                                                                                   | [`SimpleGA`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/simple_ga.py)            | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| SAMR-GA                     | [Clune et al. (2008)](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1000187)                                                    | [`SAMR_GA`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/samr_ga.py)               | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| GESMR-GA                    | [Kumar et al. (2022)](https://arxiv.org/abs/2204.04817)                                                                                                  | [`GESMR_GA`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/gesmr_ga.py)             | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| MR15-GA                     | [Rechenberg (1978)](https://link.springer.com/chapter/10.1007/978-3-642-81283-5_8)                                                                       | [`MR15_GA`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/mr15_ga.py)               | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| LGA                         | [Lange et al. (2023b)](https://arxiv.org/abs/2304.03995)                                                                                                 | [`LGA`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/lga.py)                       | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| Simple Gaussian             | [Rechenberg (1978)](https://link.springer.com/chapter/10.1007/978-3-642-81283-5_8)                                                                       | [`SimpleES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/simple_es.py)            | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| DES                         | [Lange et al. (2023a)](https://arxiv.org/abs/2211.11260)                                                                                                 | [`DES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/des.py)                       | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| LES                         | [Lange et al. (2023a)](https://arxiv.org/abs/2211.11260)                                                                                                 | [`LES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/les.py)                       | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| EvoTF                       | [Lange et al. (2024)](https://arxiv.org/abs/2403.02985)                                                                                                  | [`EvoTF_ES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/evotf_es.py)             | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| Diffusion Evolution         | [Zhang et al. (2024)](https://arxiv.org/pdf/2410.02543)                                                                                                  | [`DiffusionEvolution`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/diffusion.py)  | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| SV-OpenAI-ES                | [Liu et al. (2017)](https://arxiv.org/abs/1704.02399)                                                                                                    | [`SV_OpenES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/sv_open_es.py)          | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| SV-CMA-ES                   | [Braun et al. (2024)](https://arxiv.org/abs/2410.10390)                                                                                                  | [`SV_CMA_ES`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/sv_cma_es.py)           | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| Particle Swarm Optimization | [Kennedy & Eberhart (1995)](https://ieeexplore.ieee.org/document/488968)                                                                                 | [`PSO`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/pso.py)                       | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| Differential Evolution      | [Storn & Price (1997)](https://www.metabolic-economics.de/pages/seminar_theoretische_biologie_2007/literatur/schaber/Storn1997JGlobOpt11.pdf)            | [`DE`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/de.py)                         | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| GLD                         | [Golovin et al. (2019)](https://arxiv.org/pdf/1911.06317.pdf)                                                                                            | [`GLD`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/gld.py)                       | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| Simulated Annealing         | [Rasdi Rere et al. (2015)](https://www.sciencedirect.com/science/article/pii/S1877050915035759)                                                          | [`SimAnneal`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/sim_anneal.py)          | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)
| Random Search               | [Bergstra & Bengio (2012)](https://www.jmlr.org/papers/volume13/bergstra12a/bergstra12a.pdf)                                                             | [`RandomSearch`](https://github.com/RobertTLange/evosax/tree/main/evosax/strategies/random.py)           | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb)

## Installation ⏳

You will need Python 3.10 or later, and a working JAX installation.

Then, install `evosax` from PyPi:

```
pip install evosax
```

To upgrade to the latest version of `evosax`, you can use:

```
pip install git+https://github.com/RobertTLange/evosax.git@main
```

## Examples 📖
* 📓 [Classic ES Tasks](https://github.com/RobertTLange/evosax/blob/main/examples/01_classic_benchmark.ipynb): API introduction on Rosenbrock function (CMA-ES, Simple GA, etc.).
* 📓 [CartPole-Control](https://github.com/RobertTLange/evosax/blob/main/examples/02_mlp_control.ipynb): OpenES & PEPG on the `CartPole-v1` gym task (MLP/LSTM controller).
* 📓 [MNIST-Classifier](https://github.com/RobertTLange/evosax/blob/main/examples/03_cnn_mnist.ipynb): OpenES on MNIST with CNN network.
* 📓 [LRateTune-PES](https://github.com/RobertTLange/evosax/blob/main/examples/07_persistent_es.ipynb): Persistent/Noise-Reuse ES on meta-learning problem as in [Vicol et al. (2021)](http://proceedings.mlr.press/v139/vicol21a.html).
* 📓 [Restart-Wrappers](https://github.com/RobertTLange/evosax/blob/main/examples/06_restart_es.ipynb): Custom restart wrappers as e.g. used in (B)IPOP-CMA-ES.
* 📓 [Brax Control](https://github.com/RobertTLange/evosax/blob/main/examples/07_brax_control.ipynb): Evolve Tanh MLPs on Brax tasks using the `EvoJAX` wrapper.
* 📓 [BBOB Visualizer](https://github.com/RobertTLange/evosax/blob/main/examples/08_bbo_visualizer.ipynb): Visualize evolution rollouts on 2D fitness landscapes.

## Key Features 💵

- **Strategy Diversity**: `evosax` implements more than 30 classical and modern neuroevolution strategies. All of them follow the same simple `ask`/`eval` API and come with tailored tools such as the [ClipUp](https://arxiv.org/abs/2008.02387) optimizer, parameter reshaping into PyTrees and fitness shaping (see below).

- **Vectorization/Parallelization of `ask`/`tell` Calls**: Both `ask` and `tell` calls can leverage `jit`, `vmap`/`pmap`. This enables vectorized/parallel rollouts of different evolution strategies.

```python
from evosax.strategies.ars import ARS, Params
# E.g. vectorize over different initial perturbation stds
strategy = ARS(population_size=100, num_dims=20)
params = Params(sigma_init=jnp.array([0.1, 0.01, 0.001]), sigma_decay=0.999, ...)

# Specify how to map over ES hyperparameters 
map_dict = Params(sigma_init=0, sigma_decay=None, ...)

# Vmap-composed batch init, ask and tell functions 
batch_init = jax.vmap(strategy.init, in_axes=(None, map_dict))
batch_ask = jax.vmap(strategy.ask, in_axes=(None, 0, map_dict))
batch_tell = jax.vmap(strategy.tell, in_axes=(0, 0, 0, map_dict))
```

- **Scan Through Evolution Rollouts**: You can also `lax.scan` through entire `init`, `ask`, `eval`, `tell` loops for fast compilation of ES loops:

```python
key, subkey = jax.random.split(key)
params = strategy.default_params
state = strategy.init(subkey, params)

def step_fn(carry, _):
    state, key = carry
    key, subkey = jax.random.split(key)
    x, state = strategy.ask(subkey, state, params)
    fitness = ...
    state = strategy.tell(x, fitness, state, params)
    return (state, key), fitness

_, fitness = jax.lax.scan(
    step_fn,
    (state, key),
    length=num_steps,
)
```

- **Flexible Fitness Shaping**: By default `evosax` assumes that the fitness objective is to be minimized. If you would like to maximize instead, perform rank centering, z-scoring or add weight regularization you can use the `FitnessShaper`: 

```python
from evosax import FitnessShaper

# Instantiate jit-able fitness shaper (e.g. for Open ES)
fit_shaper = FitnessShaper(
    centered_rank=True,
    z_score=False,
    weight_decay=0.01,
    maximize=True,
)

# Shape the evaluated fitness scores
fit_shaped = fit_shaper.apply(x, fitness) 
```

## Resources & Other Great JAX-ES Tools 📝

* 📺 [Rob's MLC Research Jam Talk](https://www.youtube.com/watch?v=Wn6Lq2bexlA&t=51s): Small motivation talk at the ML Collective Research Jam.
* 📝 [Rob's 02/2021 Blog](https://roberttlange.github.io/posts/2021/02/cma-es-jax/): Tutorial on CMA-ES & leveraging JAX's primitives.
* 💻 [Evojax](https://github.com/google/evojax): JAX-ES library by Google Brain with great rollout wrappers.
* 💻 [QDax](https://github.com/adaptive-intelligent-robotics/QDax): Quality-Diversity algorithms in JAX.

## Acknowledgements & Citing `evosax` ✏️

If you use `evosax` in your research, please cite the following [paper](https://arxiv.org/abs/2212.04180):

```
@article{evosax2022github,
  author = {Robert Tjarko Lange},
  title = {evosax: JAX-based Evolution Strategies},
  journal={arXiv preprint arXiv:2212.04180},
  year = {2022},
}
```

We acknowledge financial support by the [Google TRC](https://sites.research.google/trc/about/) and the Deutsche
Forschungsgemeinschaft (DFG, German Research Foundation) under Germany's Excellence Strategy - EXC 2002/1 ["Science of Intelligence"](https://www.scienceofintelligence.de/) - project number 390523135.

## Development 👷

You can run the test suite via `python -m pytest -vv --all`. If you find a bug or are missing your favourite feature, feel free to create an issue and/or start [contributing](CONTRIBUTING.md) 🤗.

## Disclaimer ⚠️

This repository contains an independent reimplementation of LES and DES based on the corresponding ICLR 2023 publication [(Lange et al., 2023)](https://arxiv.org/abs/2211.11260). It is unrelated to Google or DeepMind. The implementation has been tested to roughly reproduce the official results on a range of tasks.
