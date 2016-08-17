import pytest
import numpy as np
from numpy.testing import assert_allclose
from keras.utils.test_utils import keras_test
from keras.layers import wrappers, Input
from keras.layers import core, convolutional, recurrent
from keras.models import Sequential, Model, model_from_json


@keras_test
def test_TimeDistributed():
    # first, test with Dense layer
    model = Sequential()
    model.add(wrappers.TimeDistributed(core.Dense(2), input_shape=(3, 4)))
    model.add(core.Activation('relu'))
    model.compile(optimizer='rmsprop', loss='mse')
    model.fit(np.random.random((10, 3, 4)), np.random.random((10, 3, 2)), nb_epoch=1, batch_size=10)

    # test config
    model.get_config()

    # compare to TimeDistributedDense
    test_input = np.random.random((1, 3, 4))
    test_output = model.predict(test_input)
    weights = model.layers[0].get_weights()

    reference = Sequential()
    reference.add(core.TimeDistributedDense(2, input_shape=(3, 4), weights=weights))
    reference.add(core.Activation('relu'))
    reference.compile(optimizer='rmsprop', loss='mse')

    reference_output = reference.predict(test_input)
    assert_allclose(test_output, reference_output, atol=1e-05)

    # test when specifying a batch_input_shape
    reference = Sequential()
    reference.add(core.TimeDistributedDense(2, batch_input_shape=(1, 3, 4), weights=weights))
    reference.add(core.Activation('relu'))
    reference.compile(optimizer='rmsprop', loss='mse')

    reference_output = reference.predict(test_input)
    assert_allclose(test_output, reference_output, atol=1e-05)

    # test with Convolution2D
    model = Sequential()
    model.add(wrappers.TimeDistributed(convolutional.Convolution2D(5, 2, 2, border_mode='same'), input_shape=(2, 3, 4, 4)))
    model.add(core.Activation('relu'))
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(np.random.random((1, 2, 3, 4, 4)), np.random.random((1, 2, 5, 4, 4)))

    model = model_from_json(model.to_json())
    model.summary()

    # test stacked layers
    model = Sequential()
    model.add(wrappers.TimeDistributed(core.Dense(2), input_shape=(3, 4)))
    model.add(wrappers.TimeDistributed(core.Dense(3)))
    model.add(core.Activation('relu'))
    model.compile(optimizer='rmsprop', loss='mse')

    model.fit(np.random.random((10, 3, 4)), np.random.random((10, 3, 3)), nb_epoch=1, batch_size=10)

    # test wrapping Sequential model
    model = Sequential()
    model.add(core.Dense(3, input_dim=2))
    outer_model = Sequential()
    outer_model.add(wrappers.TimeDistributed(model, input_shape=(3, 2)))
    outer_model.compile(optimizer='rmsprop', loss='mse')
    outer_model.fit(np.random.random((10, 3, 2)), np.random.random((10, 3, 3)), nb_epoch=1, batch_size=10)

    # test with functional API
    x = Input(shape=(3, 2))
    y = wrappers.TimeDistributed(model)(x)
    outer_model = Model(x, y)
    outer_model.compile(optimizer='rmsprop', loss='mse')
    outer_model.fit(np.random.random((10, 3, 2)), np.random.random((10, 3, 3)), nb_epoch=1, batch_size=10)


@keras_test
def test_Bidirectional():
    rnn = recurrent.SimpleRNN
    nb_sample = 1
    dim = 2
    timesteps = 2
    for mode in ['sum', 'concat']:
        x = np.random.random((nb_sample, timesteps, dim))
        output_dim = 2 if mode == 'concat' else 1
        y = np.random.random((nb_sample, output_dim))

        # test with Sequential model
        model = Sequential()
        model.add(wrappers.Bidirectional(rnn(1),
                                         merge_mode=mode, input_shape=(timesteps, dim)))
        model.compile(loss='mse', optimizer='sgd')
        model.fit(x, y, nb_epoch=1, batch_size=1)

        # test config
        model.get_config()
        model = model_from_json(model.to_json())
        model.summary()

        # test stacked bidirectional layers
        model = Sequential()
        model.add(wrappers.Bidirectional(rnn(1, return_sequences=True),
                                         merge_mode=mode, input_shape=(timesteps, dim)))
        model.add(wrappers.Bidirectional(rnn(1), merge_mode=mode))
        model.compile(loss='mse', optimizer='sgd')
        model.fit(x, y, nb_epoch=1, batch_size=1)

        # test with functional API
        input = Input((timesteps, dim))
        output = wrappers.Bidirectional(rnn(1), merge_mode=mode)(input)
        model = Model(input, output)
        model.compile(loss='mse', optimizer='sgd')
        model.fit(x, y, nb_epoch=1, batch_size=1)


if __name__ == '__main__':
    pytest.main([__file__])
