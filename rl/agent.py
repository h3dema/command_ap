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

import sys
import argparse
import logging
# import numpy as np
# from mab import EpsilonGreedyAbstract
from mab import UCBAbstract
from reward import reward

# *** não precisa das linhas abaixo !!!!
# if np.any(['get-set' in v for v in sys.path]):
#     """add path to client"""
#     sys.path.append('../get-set')


#
# set log
#
LOG = logging.getLogger('AGENT')


#
# this is the real class
# you should implement only the run_action method
# this method interacts with the environment, performing the action and collection the reward
# it returns if the agent was able to perform the action
#
class MABAgent(UCBAbstract):

    def run_action(self, action):
        """
            :return r: the reward of the action taken
            :return success: boolean value indicating if the agent could perform the action or not
        """
        LOG.info("Running action {}".format(action))
        # decode the int "action" into the real action

        # call the environment to perform the action

        # get the reward if the action was performed
        r = reward(qos, power)

        return 0, False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the RL agent')
    parser.add_argument('--n-actions', type=int, default=None, help='Inform the number of actions the RL agent can perform')
    parser.add_argument('--double-trick', action="store_true", help='Perform the double trick in the timestep')
    parser.add_argument('--T', type=int, default=2, help='initial value for double trick')
    parser.add_argument('--debug', action="store_true", help='log debug info')
    args = parser.parse_args()

    if args.n_actions is None:
        LOG.info("You should define the number of actions to execute")
        parser.print_help()
        sys.exit(1)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    agent = MABAgent(n_actions=args.n_actions)
    t = 1
    T = args.T
    in_loop = True
    while in_loop:
        """runs forever or until CTRL+C is pressed"""
        try:
            a = agent.get_action()
            r, success = agent.run_action(a)
            if success:
                agent.update(a, r)
            else:
                LOG.debug("timestep {} -- action {} failed -- no reward".format(t, a))
            t += 1
            if args.double_trick and t > T:
                t = 1
                agent.reset_pulls()
                try:
                    T = 2 * T
                except OverflowError:
                    T = args.T
        except KeyboardInterrupt:
            """exit with CTRL+c"""
            in_loop = False
