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
import time
import sys
import argparse
import logging
import numpy as np
import pickle
import http.client
import urllib.parse

# import numpy as np
# from mab import EpsilonGreedyAbstract
from mab import UCBAbstract
from reward import calc_reward
from model import get_QoS

#
# set log
#
LOG = logging.getLogger('AGENT')


def send_command(server, port, interface, cmd):
    conn = http.client.HTTPConnection(args.server, args.port)
    url = "{}?{}".format(cmd, urllib.parse.urlencode({'iface': interface}))
    conn.request(method='GET', url=url)
    resp = conn.getresponse()
    LOG.debug("status {}".format(resp.status))
    if resp.status == 200:
        data = pickle.loads(resp.read())
        LOG.debug("received {}".format(data.values()))
        return data.values()
    else:
        return dict()  # error ??


def set_power(server, port, interface, new_power):
    conn = http.client.HTTPConnection(args.server, args.port)
    url = "{}?{}".format('set_power', urllib.parse.urlencode({'iface': interface, 'new_power': new_power}))
    conn.request(method='GET', url=url)
    conn.getresponse()


def get_power(server, port, interface):
    r = send_command(server, port, interface, 'get_power')
    txp = r.get('txpower', 0) if r is not None else 0
    LOG.info('txpower {}'.format(txp))
    return txp


def get_features(server, port, interface):
    return send_command(server, port, interface, 'get_features')


#
# this is the real class
# you should implement only the run_action method
# this method interacts with the environment, performing the action and collection the reward
# it returns if the agent was able to perform the action
#
class MABAgent(UCBAbstract):

    def __init__(self, n_actions, server, port, interface):
        super().__init__(n_actions)
        self.server = server
        self.port = port
        self.interface = interface

    def run_action(self, action):
        """
            :return r: the reward of the action taken
            :return success: boolean value indicating if the agent could perform the action or not
        """
        # decode the int "action" into the real action
        power = action + 1  # add 1, because get_action() returns 0 to n_actions - 1
        LOG.info("Running action {} - sets power to {}".format(action, power))

        # call the environment to perform the action
        set_power(self.server, self.port, self.interface, power)

        # get the reward if the action was performed
        features = get_features(self.server, self.port, self.interface)  # contain features with all stations
        #
        # testar aqui se features retornou algo util, ou se foi erro !!
        #

        # *** **** *** ***
        #
        #
        # temos que chamar para cada estação, para achar o qos de cada uma
        # este loop está errado, tem que conferir como retorna features para identificarmos a estação
        #
        #
        # *** **** *** ***
        rewards = []
        for stations in features:
            raise Exception("implement the line below")
            # *** **** *** ***
            #
            #
            # features_da_estacao contem as features especificas da estação
            # temos que chamar para cada estação
            #
            # *** **** *** ***
            calc_qos = get_QoS(features_da_estacao)
            r = calc_reward(calc_qos, power)
            rewards.append(r)
        reward = np.average(rewards)

        return reward, False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the RL agent')
    # arg "n-actions" considers 15 power setups
    parser.add_argument('--n-actions', type=int, default=15, help='Inform the number of actions the RL agent can perform')
    parser.add_argument('--double-trick', action="store_true", help='Perform the double trick in the timestep')
    parser.add_argument('--T', type=int, default=2, help='initial value for double trick')
    parser.add_argument('--debug', action="store_true", help='log debug info')
    parser.add_argument('--interval', type=int, default=1, help='interval between evaluations')

    parser.add_argument('--server', type=str, default='localhost', help='Set the AP address')
    parser.add_argument('--port', type=int, default=8080, help='Set the AP port')

    # *** **** *** ***
    #
    #
    # Marcos colocar aqui o nome certo da interface
    #
    #
    # *** **** *** ***
    parser.add_argument('--interface', type=str, default='wlan0', help='AP wlan interface')

    args = parser.parse_args()

    if args.n_actions is None:
        LOG.info("You should define the number of actions to execute")
        parser.print_help()
        sys.exit(1)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    agent = MABAgent(n_actions=args.n_actions,
                     server=args.server, port=args.port, interface=args.interface)
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
            time.sleep(args.interval)
        except KeyboardInterrupt:
            """exit with CTRL+c"""
            in_loop = False
