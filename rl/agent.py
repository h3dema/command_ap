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
import joblib
import argparse
import logging
import numpy as np
import pickle
import http.client
import urllib.parse
from collections import defaultdict
import pandas as pd
# from mab import EpsilonGreedyAbstract
from mab import UCBAbstract
from reward import calc_reward
from model import get_QoS
from model import create_window
# import time to debug
import time
# import keras
from keras.models import load_model
from keras.models import Sequential, Model
from keras.layers import Input
from keras.layers import Conv1D, GRU, LSTM
from keras.layers import MaxPooling1D, AveragePooling1D
from keras.layers import Dense, Dropout, Flatten
from keras import metrics
import datetime

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
        return data
    else:
        return dict()  # error ??


def set_power(server, port, interface, new_power):
    conn = http.client.HTTPConnection(args.server, args.port)
    url = "{}?{}".format('/set_power', urllib.parse.urlencode({'iface': interface, 'new_power': new_power}))
    conn.request(method='GET', url=url)
    conn.getresponse()


def get_power(server, port, interface):
    r = send_command(server, port, interface, '/get_power')
    txp = r.get('txpower', 0) if r is not None else 0
    LOG.info('txpower {}'.format(txp))
    return txp


def get_features(server, port, interface):
    return send_command(server, port, interface, '/get_features')


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
        self.cat = defaultdict(list)
        self.cbt = defaultdict(list)
        self.crt = defaultdict(list)
        self.ctt = defaultdict(list)
        self.txf = defaultdict(list)
        self.txr = defaultdict(list)
        self.txp = defaultdict(list)
        self.txb = defaultdict(list)
        self.rxdrop = defaultdict(list)
        self.rxb = defaultdict(list)
        self.rxp = defaultdict(list)

        self.catDataFrame = defaultdict(list)
        self.cbtDataFrame = defaultdict(list)
        self.crtDataFrame = defaultdict(list)
        self.cttDataFrame = defaultdict(list)
        self.txfDataFrame = defaultdict(list)
        self.txrDataFrame = defaultdict(list)
        self.txpDataFrame = defaultdict(list)
        self.txbDataFrame = defaultdict(list)
        self.rxdropDataFrame = defaultdict(list)
        self.rxbDataFrame = defaultdict(list)
        self.rxpDataFrame = defaultdict(list)
        self.avg_signal = defaultdict(list)
        self.dataFrameAvg_signal = defaultdict(list)
        self.dataFrameTxPower = defaultdict(list)
        self.num_station = defaultdict(list)
        self.dataFrame = pd.DataFrame()
        self.indexIloc = 0
        self.dataFrameTx_bitrate = defaultdict(list)
        self.dataFrameRx_bitrate = defaultdict(list)
        self.rewards = []
        """
            TODO: model from parameter
        """
        self.model = load_model("best_model_epoch_269_bps.h5")
        self.scaler = joblib.load('/opt/Projects/command_ap/rl/minmax_final_scaler.pkl')

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
        
        for k, v in features.items():
            self.cat[k].append(v.get("cat",None))
            self.cbt[k].append(v.get("cbt",None))
            self.crt[k].append(v.get("crt",None))
            self.ctt[k].append(v.get("ctt",None))
            self.txf[k].append(v.get("txf",None))
            self.txr[k].append(v.get("txr",None))
            self.txp[k].append(v.get("txp",None))
            self.txb[k].append(v.get("txb",None))
            self.rxdrop[k].append(v.get("rxdrop",None))
            self.rxb[k].append(v.get("rxb",None))
            self.rxp[k].append(v.get("rxp",None))
            
            if(len(self.cat[k]) > 1):
                # iw trended data
                self.catDataFrame[k].append(self.cat[k][1] - self.cat[k][0])
                self.cbtDataFrame[k].append(self.cbt[k][1] - self.cbt[k][0])
                self.crtDataFrame[k].append(self.crt[k][1] - self.crt[k][0])
                self.cttDataFrame[k].append(self.ctt[k][1] - self.ctt[k][0])
                self.txfDataFrame[k].append(self.txf[k][1] - self.txf[k][0])
                self.txrDataFrame[k].append(self.txr[k][1] - self.txr[k][0])
                self.txpDataFrame[k].append(self.txp[k][1] - self.txp[k][0])
                self.txbDataFrame[k].append(self.txb[k][1] - self.txb[k][0])
                self.rxdropDataFrame[k].append(self.rxdrop[k][1] - self.rxdrop[k][0])
                self.rxbDataFrame[k].append(self.rxb[k][1] - self.rxb[k][0])
                self.rxpDataFrame[k].append(self.rxp[k][1] - self.rxp[k][0])

                self.dataFrameAvg_signal[k].append(v.get("avg_signal", None))
                self.dataFrameTxPower[k].append(v.get("tx_power", None))
                self.num_station[k].append(v.get("num_stations", None))
                self.dataFrameTx_bitrate[k].append(v.get("tx_bitrate", None))
                self.dataFrameRx_bitrate[k].append(v.get("rx_bitrate", None))

                self.dictFrame = {  'num_station': self.num_station[k],
                                    'tx_power': self.dataFrameTxPower[k],
                                    'cat':self.catDataFrame[k],
                                    'cbt':self.cbtDataFrame[k], 
                                    'crt': self.crtDataFrame[k],
                                    'ctt': self.cttDataFrame[k],
                                    'avg_signal':self.dataFrameAvg_signal[k],
                                    'txf': self.txfDataFrame[k],
                                    'txr': self.txrDataFrame[k],
                                    'txp': self.txpDataFrame[k],
                                    'txb': self.txbDataFrame[k],
                                    'rxdrop': self.rxdropDataFrame[k],
                                    'rxb': self.rxbDataFrame[k],
                                    'rxp': self.rxpDataFrame[k],
                                    'tx_bitrate': self.dataFrameTx_bitrate[k],
                                    'rx_bitrate': self.dataFrameRx_bitrate[k],
                                    'bps': 0,
                                    'delay': 0,
                                    'jitter': 0,
                                    'loss': 0                                   
                                    }
                                    
                self.dataFrame = pd.DataFrame(data=self.dictFrame)
                """
                    TODO: Check MIN MAX
                """
                
                """
                    TODO: get the timestamp from the parameters.
                        using timestamp 3
                """
                # ignore the first two
                if len(self.dataFrame) > 2:
                    
                    window = create_window(self.scaler.transform(self.dataFrame.iloc[self.indexIloc :self.indexIloc +  3].values), 3)
                    X = window[:,:,:16]                
                    calc_qos = self.model.predict(X)
                    LOG.info("Time {} - MAC {} - QoS prediction {}".format(datetime.datetime.now().timestamp(), k, (calc_qos) * (self.scaler.data_max_[16:17] - self.scaler.data_min_[16:17]) + self.scaler.data_min_[16:17]))
                    
                    r = calc_reward(calc_qos, power)
                    self.rewards.append(r)
                # delete first iten
                del self.cat[k][0:1]
                del self.cbt[k][0:1]
                del self.crt[k][0:1]
                del self.ctt[k][0:1]
                del self.txf[k][0:1]
                del self.txr[k][0:1]
                del self.txp[k][0:1]
                del self.txb[k][0:1]
                del self.rxdrop[k][0:1]
                del self.rxb[k][0:1]
                del self.rxp[k][0:1]
            
        if len(self.dataFrame) > 2:
            self.indexIloc = self.indexIloc + 1
        reward = np.average(self.rewards)
        LOG.info("Reward average {}".format(reward))
        time.sleep(1)
        return reward, True


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
