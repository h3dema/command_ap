#!/usr/bin/python
"""
    runs the agent:
    python3 agent.py


    the --double-trick parameter uses the trick suggested by xxx, since MAB was not meant to run forever.
    If it is active, time periods of T iterations will be considered,
    and for each T iteractions this period is increased to 2T.
    --T define the initial period.

"""
__author__ = "Henrique Moura"
__copyright__ = "Copyright 2018, h3dema"
__credits__ = ["Henrique Moura"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Henrique Moura"
__email__ = "h3dema@gmail.com"
__status__ = "Production"

import numpy as np


def reward(qos, power):
    """ this function goes to the agent
        it receives two scaled parameters (between 0 and 1), and
        returns the reward between 0 and 1
    """
    if qos < 0.62:
        r = min((np.square(qos) + np.square(power) / 5.0) / 0.6, 0.6)
    else:
        r = max(1 - (np.square(qos - 1) + np.square(power) / 20.0) / 0.285, 0.6)
    return r

