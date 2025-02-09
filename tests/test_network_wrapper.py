import jax
import jax.numpy as jnp
from evosax.networks import CNN, MLP, All_CNN_C


def test_mlp_forward():
    key = jax.random.key(0)
    network = MLP(
        num_hidden_units=64,
        num_hidden_layers=2,
        num_output_units=1,
        hidden_activation="relu",
        output_activation="identity",
    )
    solution = jnp.zeros((4,))
    params = network.init(
        key,
        x=solution,
        key=key,
    )
    out = jax.jit(network.apply)(params, solution, key)
    assert out.shape == (1,)


# def test_lstm_forward():
#     key = jax.random.key(0)
#     network = LSTM(
#         num_hidden_units=32,
#         num_output_units=1,
#         output_activation="identity",
#     )
#     solution = jnp.zeros((4,))
#     carry_init = network.init_carry()
#     params = network.init(
#         key,
#         x=solution,
#         carry=carry_init,
#         key=key,
#     )
#     _, out = jax.jit(network.apply)(params, solution, carry_init, key)
#     assert out.shape == (1,)


def test_cnn_forward():
    key = jax.random.key(0)
    network = CNN(
        depth_1=1,
        depth_2=1,
        features_1=16,
        features_2=8,
        kernel_1=3,
        kernel_2=5,
        strides_1=1,
        strides_2=1,
        num_linear_layers=1,
        num_hidden_units=16,
        num_output_units=10,
    )
    solution = jnp.zeros((1, 28, 28, 1))
    params = network.init(
        key,
        x=solution,
        key=key,
    )
    out = jax.jit(network.apply)(params, solution, key)
    assert out.shape == (1, 10)


def test_all_cnn_forward():
    key = jax.random.key(0)
    network = All_CNN_C(
        depth_1=1,
        depth_2=1,
        features_1=16,
        features_2=8,
        kernel_1=3,
        kernel_2=5,
        strides_1=1,
        strides_2=1,
        final_window=(28, 28),
        num_output_units=10,
    )
    solution = jnp.zeros((1, 28, 28, 1))
    params = network.init(
        key,
        x=solution,
        key=key,
    )
    out = jax.jit(network.apply)(params, solution, key)
    assert out.shape == (1, 10)
