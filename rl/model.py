#!/usr/bin/python
"""

    This module calculates the QoS based on the features

"""

import keras
import numpy as np

def get_QoS(features):
    raise Exception("Implement get_QoS")
    pass

def create_window(data_values, __timesteps):
    data_values = data_values.reshape(data_values.shape[0], 1, data_values.shape[1])
    ds = np.zeros((1, __timesteps, data_values.shape[2]))
    for j in range(0, data_values.shape[0] - __timesteps + 1):

        window = data_values[j:j + 1, :, :]

        for k in range(1, __timesteps):
            window = np.append(window, data_values[j + k:j + k + 1, :, :], axis=1)

        ds = np.append(ds, window, axis=0)
    return ds[1:, :, :]