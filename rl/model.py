#!/usr/bin/python
"""

    This module calculates the QoS based on the features

"""

import numpy as np


def get_QoS(model, features):
    """ TODO: implement this, using the model and the features
        use keras model to predict the QoS based on the features
    """
    raise Exception("Implement get_QoS")
    pass


def create_window(data_values, timesteps):
    """ convert the data_values into the format needed by the keras model
        @param data_values:
        @param timesteps: number of time steps
    """
    data_values = data_values.reshape(data_values.shape[0], 1, data_values.shape[1])
    ds = np.zeros((1, timesteps, data_values.shape[2]))
    for j in range(0, data_values.shape[0] - timesteps + 1):

        window = data_values[j:j + 1, :, :]

        for k in range(1, timesteps):
            window = np.append(window, data_values[j + k:j + k + 1, :, :], axis=1)

        ds = np.append(ds, window, axis=0)
    return ds[1:, :, :]
