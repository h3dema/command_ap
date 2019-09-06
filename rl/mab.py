#!/usr/bin/python
"""

    This module define three abstract MAB agents:
    * RandomAbstract: select random actions
    * EpsilonGreedyAbstract: select action using an epsilon-greedy policy
    * UCBAbstract: selects actions based on the UCB policy

"""
__author__ = "Henrique Moura"
__copyright__ = "Copyright 2018, h3dema"
__credits__ = ["Henrique Moura"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Henrique Moura"
__email__ = "h3dema@gmail.com"
__status__ = "Production"

import logging
import numpy as np
from abc import abstractmethod

#
# set log
#
LOG = logging.getLogger('MAB')


def softmax(x):
    """ returns the softmax function (probabilities) given an array x

        @param x: float
        @return: softmax(x)
        @rtype: float
    """
    return np.exp(x) / sum(np.exp(x))


class MAB(object):

    def __init__(self, n_actions):
        """ creates the agent handler

            @param n_actions: number of actions the agent can perform from [0, n_actions - 1]
            @type n_actions: int
        """
        self.n_actions = n_actions

        self._total_pulls = 0
        self.avg = np.zeros(n_actions)
        self.n_visited = np.zeros(n_actions)
        LOG.info("Created agent with {} actions".format(n_actions))

    @abstractmethod
    def get_action(self):
        """ Get current best action

            @return: the selected action according to the policy
            @rtype: int
        """
        pass

    @abstractmethod
    def run_action(self, action):
        """
            @return: r, success
                    'r' is the reward of the action taken, and 'success' is boolean value indicating if the agent could perform the action or not
            @rtype float, bool
        """
        pass

    def reset_pulls(self):
        """reset the number of executions to zero."""
        self._total_pulls = 0

    def update(self, action, reward):
        """ observe the reward from action and update agent's internal parameters
            @param action: the action 'a' taken
            @param reward: the reward obtained by taking action 'a'
        """
        self._total_pulls += 1
        self.n_visited[action] += 1
        self.avg[action] = (self.avg[action] * (self.n_visited[action] - 1) + reward) / self.n_visited[action]
        LOG.debug("#{} action selected -- num.trials {} -- new avg = {}".format(action, self.n_visited[action], self.avg[action]))

    @property
    def name(self):
        """ name of the class """
        return self.__class__.__name__


class RandomAbstract(MAB):
    """
    this class implements the random policy
    """

    def get_action(self):
        """ returns a random action

            @return: the selected action
            @rtype: int
        """
        a = np.random.randint(0, self.n_actions)
        LOG.debug("Iter {:5d}: Action selected {}".format(self._total_pulls, a))
        return a


class EpsilonGreedyAbstract(MAB):
    """
    this class implements the epsilon-greedy policy
    """

    def __init__(self, n_actions, epsilon=0.01):
        super().__init__(n_actions)
        self._epsilon = epsilon
        LOG.info("Created epsilon-greedy agent: actions={} epsilon={}".format(self.n_actions, epsilon))

    def get_action(self):
        """selects the action to be taken based on the epsilon-greedy policy

            @return: the selected action
            @rtype: int
        """
        a = np.argmax(self.avg)
        if np.random.random() < self._epsilon:
            a = np.random.randint(self.n_actions)
        LOG.debug("Iter {:5d}: Action selected {}".format(self._total_pulls, a))
        return a


#
# this class implements the UCB policy
#
class UCBAbstract(MAB):

    def __init__(self, n_actions, C=1, b=2):
        """ the defaults of C and b define a UCB1 policy
        """
        np.seterr(divide='ignore', invalid='ignore')
        super().__init__(n_actions)
        self._C = C
        self._b = b
        LOG.info("Created UCB agent: C={} b={}".format(C, b))

    @property
    def w(self):
        __w = self.avg + self._C * np.sqrt(self._b * np.log(self._total_pulls) / self.n_visited)
        return __w

    def get_prob(self):
        """returns the probability of each action using SOFTMAX"""
        return softmax(self.w)

    def get_action(self):
        """selects the action to be taken based on the UCB policy

            @return: the selected action
            @rtype: int
        """
        a = np.argmax(self.w)
        LOG.debug("Iter {:5d}: Action selected {}".format(self._total_pulls, a))
        return a


class Boltzmann(UCBAbstract):

    def get_action(self):
        """ selects the action to be taken based on the softmax policy

            @return: the selected action
            @rtype: int
        """
        p = self.get_prob()
        # select 1 action among n_actions using the probabilities
        a = np.random.choice(self.n_actions, 1, p=p)
        return a

