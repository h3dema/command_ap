#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
    server that accepts requests from an http client
    used to send commands to the AP


    Usage from command line:
    -------------------

    python3 -m get_set.server.py [--port 8080]


    Usage from program:
    -------------------

    import get_set.server
    server.run(port)


    Requirements
    ------------
    iw 4.9+  (https://git.kernel.org/pub/scm/linux/kernel/git/jberg/iw.git/snapshot/iw-4.9.tar.gz)
    iwconfig version 30
"""
import argparse
import pickle
import logging
import os
import numpy as np
from threading import Thread
from datetime import datetime
import json

import urllib.parse
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

# command processed by the AP
from cmd.command_ap import get_ifconfig
from cmd.command_ap import get_iw_info
from cmd.command_ap import get_iwconfig_info
from cmd.command_ap import get_config
from cmd.command_ap import get_power
from cmd.command_ap import set_iw_power
from cmd.command_ap import get_iw_stations
from cmd.command_ap import trigger_scan
from cmd.command_ap import get_iw_survey
from cmd.command_ap import get_iw_scan
from cmd.command_ap import get_iw_scan_mac
from cmd.command_ap import get_xmit
from cmd.command_ap import get_phy_with_wlan
from cmd.command_ap import change_channel

from get_set.server_ffox import SrvPosts
from get_set.server_ffox import ffox_memory


logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger('REST_SERVER')


# creates a global var 'httpd' that receives the httpd handle that runs in the thread,
# so we can stop it when CTRL-C is hit
httpd = None
last_rt = dict()  # save data from AP
last_tx_bytes = None  # save last read tx_bytes in MOS AP
last_ampdu = None
MAX_REPORTED_BITRATE = 20000.0
MAXIMUM_TX_BITRATE = 54.0
MAX_TX_BYTES_WIFI = MAXIMUM_TX_BITRATE * 1024 * 1024


class myHandler(BaseHTTPRequestHandler):
    """"This class will handles any incoming request from the browser
    """
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)

    @property
    def query(self):
        """parses the HTML query field"""
        q = urllib.parse.urlparse(self.path).query
        return urllib.parse.parse_qs(q)

    def send_error(self):
        """returns to the web client a 404 error"""
        self.send_response(404)  # Not found
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        # Send the html message
        self.wfile.write("Command unknown".encode())

    def send_dictionary(self, d):
        """ returns to the web client a dictionary containing the data.
            the client should use pickle.loads() to reconvert the data to a python object
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        msg = pickle.dumps(d, protocol=pickle.HIGHEST_PROTOCOL)
        self.wfile.write(msg)

    def info(self):
        """ process /get_info

        @return: dictionary
            {'wiphy': '0', 'Interface': 'wlan0', 'addr': 'b0:aa:ab:ab:ac:11',
             'width': '20MHz,', 'channel': '6',
             'txpower': '1.00 dBm', 'ssid': 'ethanolQL1', 'type': 'AP',
             'ifindex': '3', 'frequency': '2437MHz,',
             'wdev': '0x1', 'center1': '2437MHz'}
        @rtype: dict
        """
        iface = self.query.get('iface', [''])[0]
        info = get_iw_info(interface=iface)
        LOG.debug(info)
        self.send_dictionary(info)

    def iwconfig(self):
        """ process /get_iwconfig

        @return: dictionary
        {'Power Management': 'off', 'RTS thr': 'off', 'IEEE': '802.11bgn',
         'Mode': 'Master', 'Retry short limit': 7, 'Fragment thr': 'off',
         'interface': 'wlan0'}

        """
        iface = self.query.get('iface', ['wlan0'])[0]
        r = get_iwconfig_info(interface=iface)
        self.send_dictionary(r)

    def ifconfig(self):
        """ process /get_ifconfig

        @return:
            {'iface': 'wlan0',
             'rx_bytes': '2986426585', 'rx_overruns': '0', 'rx_dropped': '0',
             'rx_packets': '30257063', 'rx_scale_bytes': '2.9', 'rx_errors': '0'
             'tx_scale_bytes': '53.9', 'tx_bytes': '53923422941', 'tx_dropped': '0',
             'tx_packets': '43083207', 'tx_overruns': '0', 'tx_errors': '0',
             'collisions': '0', 'frame': '0',
             'txqueuelen': '1000',
             'carrier': '0',
             }

        """
        iface = self.query.get('iface', ['wlan0'])[0]
        r = get_ifconfig(interface=iface)
        self.send_dictionary(r)

    def get_power(self):
        """ process /get_power

        @return: the tx power of iface
        """
        iface = self.query.get('iface', ['wlan0'])[0]
        pwr = get_power(interface=iface)
        self.send_dictionary({'txpower': pwr})

    def set_power(self):
        """ process /set_power

            @return: set the tx power of iface to new_power
        """
        iface = self.query.get('iface', ['wlan0'])[0]
        new_power = self.query.get('new_power', [-1])[0]
        if len(new_power) > 0:
            set_iw_power(interface=iface, new_power=new_power)
        self.send_dictionary({'txpower': new_power})

    def set_channel(self):
        """ process /set_channel

            @return: new channel in a dictionary format {'channel': new_channel}
            @rtype: dict
        """
        iface = self.query.get('iface', ['wlan0'])[0]
        new_channel = int(self.query.get('new_channel', [-1])[0])
        change_channel(interface=iface, new_channel=new_channel)
        self.send_dictionary({'channel': new_channel})

    def xmit(self):
        """ process /get_xmit

            @return: dictionary
            {'TXOP Exceeded_VO': '0', 'TX-Pkts-All_VO': '4441336', 'FIFO Underrun_BK': '0',
             'HW-put-tx-buf_BK': '0', 'DELIM Underrun_VI': '0', 'MPDUs Queued_BE': '866',
             'DESC CFG Error_VO': '0', 'Aggregates_BK': '0', 'FIFO Underrun_VO': '0',
             'DESC CFG Error_VI': '0', 'AMPDUs Queued HW_VI': '0', 'TX-Pkts-All_BE': '42978693', 'TX-Pkts-All_VI': '0', 'DELIM Underrun_BK': '0', 'MPDUs Completed_BK': '0', 'DELIM Underrun_VO': '0', 'AMPDUs XRetried_BE': '1086', 'TX-Failed_BE': '0', 'AMPDUs XRetried_VI': '0', 'DATA Underrun_VI': '0', 'DESC CFG Error_BK': '0', 'TXERR Filtered_BK': '0', 'HW-put-tx-buf_BE': '34862773', 'AMPDUs Retried_VO': '0', 'TX-Pkts-All_BK': '0', 'TX-Failed_VO': '0', 'TXTIMER Expiry_VI': '0', 'DESC CFG Error_BE': '3', 'AMPDUs Completed_BE': '8317901', 'TX-Failed_BK': '0', 'HW-tx-start_BK': '0', 'TXTIMER Expiry_BK': '0', 'AMPDUs Queued HW_BK': '0', 'FIFO Underrun_BE': '2', 'Aggregates_BE': '1286133', 'AMPDUs Completed_VI': '0', 'AMPDUs Queued SW_BE': '42978305', 'AMPDUs Retried_BE': '811701', 'HW-put-tx-buf_VO': '4441003', 'TX-Bytes-All_VI': '0', 'TX-Bytes-All_BK': '0', 'AMPDUs Queued HW_BE': '0', 'MPDUs XRetried_VI': '0', 'MPDUs Queued_VI': '0', 'Aggregates_VI': '0', 'DATA Underrun_BK': '0', 'MPDUs Completed_VO': '4435505', 'MPDUs XRetried_BK': '0', 'MPDUs Queued_VO': '4280885', 'Aggregates_VO': '0', 'TXOP Exceeded_BK': '0', 'AMPDUs Queued SW_BK': '0', 'FIFO Underrun_VI': '0', 'HW-put-tx-buf_VI': '0', 'MPDUs XRetried_VO': '5831', 'AMPDUs Queued HW_VO': '0', 'TXERR Filtered_VO': '412', 'DELIM Underrun_BE': '0', 'TX-Bytes-All_BE': '2498976381', 'DATA Underrun_BE': '0', 'HW-tx-proc-desc_BK': '0', 'HW-tx-start_BE': '0', 'MPDUs XRetried_BE': '42463', 'TXERR Filtered_VI': '0', 'AMPDUs Queued SW_VI': '0', 'TX-Bytes-All_VO': '796749298', 'AMPDUs Completed_VO': '0', 'TXOP Exceeded_BE': '0', 'AMPDUs XRetried_BK': '0', 'DATA Underrun_VO': '0', 'MPDUs Completed_VI': '0', 'AMPDUs Retried_VI': '0', 'AMPDUs Queued SW_VO': '160451', 'TXOP Exceeded_VI': '0', 'HW-tx-proc-desc_BE': '39331824', 'HW-tx-proc-desc_VI': '0', 'AMPDUs Retried_BK': '0', 'HW-tx-start_VI': '0', 'AMPDUs XRetried_VO': '0', 'TXTIMER Expiry_VO': '0', 'TXERR Filtered_BE': '108810', 'HW-tx-proc-desc_VO': '4441078', 'TX-Failed_VI': '0', 'MPDUs Queued_BK': '0', 'TXTIMER Expiry_BE': '0', 'MPDUs Completed_BE': '34617243', 'AMPDUs Completed_BK': '0', 'HW-tx-start_VO': '0'}
            @rtype: dict
        """
        phy_iface = self.query.get('phy', ['phy0'])[0]
        r = get_xmit(phy_iface)
        self.send_dictionary(r)

    def get_stations(self):
        """ process /num_stations

            @return:
            {'54:e6:fc:da:ff:34': {'short slot time': 'yes', 'DTIM period': 2.0,
                                   'authorized': 'yes',
                                   'tx bitrate': 1.0,
                                   'tx bytes': 322.0, 'tx packets': 2.0, 'tx failed': 0.0,
                                   'rx bitrate': 1.0
                                   'rx bytes': 288.0, 'rx drop misc': 1.0, 'rx packets': 2.0,
                                   'preamble': 'short',
                                   'WMM/WME': 'yes',
                                   'signal avg': 58.0, 'MFP': 'no',
                                   'beacon interval': 100.0, 'signal': 57.0,
                                   'tx retries': 1.0,
                                   'authenticated': 'yes', 'TDLS peer': 'no',
                                   'connected time': 0.0, 'inactive time': 4.0, 'associated': 'yes',
                                   }
             }
            @rtype: dict
        """
        iface = self.query.get('iface', ['wlan0'])[0]
        stations = get_iw_stations(interface=iface)
        self.send_dictionary(stations)

    def get_num_stations(self):
        """ process /get_num_stations

        @return: number of stations
        @rtype: int
        """
        iface = self.query.get('iface', ['wlan0'])[0]
        stations = get_iw_stations(interface=iface)
        self.send_dictionary({'num_stations': len(stations)})

    def get_survey(self):
        """
            @return:
                {2432: {'channel busy time': 394.0, 'channel receive time': 285.0, 'channel transmit time': 81.0, 'noise': 81.0, 'channel active time': 1104.0},
                 2437: {'in use': True, 'channel receive time': 1073537372.0, 'noise': 80.0, 'channel busy time': 1163590333.0, 'channel transmit time': 60790348.0, 'channel active time': 3628159621.0},
                 2442: {'channel busy time': 682.0, 'channel receive time': 336.0, 'channel transmit time': 310.0, 'noise': 81.0, 'channel active time': 1121.0}, 2412: {'channel busy time': 722824.0, 'channel receive time': 505677.0, 'channel transmit time': 204390.0, 'noise': 80.0, 'channel active time': 1681119.0}, 2447: {'channel busy time': 194.0, 'channel receive time': 135.0, 'channel transmit time': 27.0, 'noise': 81.0, 'channel active time': 1121.0}, 2417: {'channel busy time': 351.0, 'channel receive time': 316.0, 'channel transmit time': 19.0, 'noise': 80.0, 'channel active time': 1200.0}, 2452: {'channel busy time': 242.0, 'channel receive time': 167.0, 'channel transmit time': 27.0, 'noise': 80.0, 'channel active time': 1127.0}, 2422: {'channel busy time': 240.0, 'channel receive time': 189.0, 'channel transmit time': 17.0, 'noise': 80.0, 'channel active time': 1165.0}, 2457: {'channel busy time': 458.0, 'channel receive time': 419.0, 'channel transmit time': 19.0, 'noise': 80.0, 'channel active time': 1110.0}, 2427: {'channel busy time': 823.0, 'channel receive time': 193.0, 'channel transmit time': 575.0, 'noise': 81.0, 'channel active time': 3462.0}, 2462: {'channel busy time': 2614.0, 'channel receive time': 1448.0, 'channel transmit time': 1085.0, 'noise': 80.0, 'channel active time': 3320.0}}
                 2467: {},
                 2472: {},
            @rtype: dict
        """
        iface = self.query.get('iface', ['wlan0'])[0]
        survey = get_iw_survey(interface=iface)
        self.send_dictionary(survey)

    def get_scan(self):
        """ returns the partial results from iw scan dump

            {'50:c7:bf:3b:db:37': {'channel': '1',
                                   'SSID': 'LAC',
                                   'TSF': '0d, 05:19:27',
                                   'last seen': 104,
                                   'freq': 2412,
                                   'signal': -54.0,
                                   'beacon interval': 100},
             '84:b8:02:44:07:d2': {'channel': '1',
                                   'SSID': 'DCC-usuarios',
                                   'TSF': '27d, 03:24:26',
                                   'last seen': 1024,
                                   'freq': 2412,
                                   'signal': -58.0,
                                   'beacon interval': 102}
             }
        """
        iface = self.query.get('iface', ['wlan0'])[0]
        trigger_scan(interface=iface)
        aps = get_iw_scan(interface=iface)
        self.send_dictionary(aps)

    def get_scan_mac(self):
        """ return the result from iw scan dump
            @return: list[str] each entry is a detected mac
        """
        iface = self.query.get('iface', ['wlan0'])[0]
        trigger_scan(interface=iface)
        aps = get_iw_scan_mac(interface=iface)
        self.send_dictionary(aps)

    def get_config(self):
        """ return the result from hostapd_cli get_config

            @return: {'group_cipher': 'CCMP', 'key_mgmt': 'WPA-PSK ', 'rsn_pairwise_cipher': 'CCMP',
             'ssid': 'ethanolQL1', 'bssid': 'b0:aa:ab:ab:ac:11',
             'wps_state': 'disabled'}
            @rtype: dict
        """
        conf = get_config()
        self.send_dictionary(conf)

    def hello(self):
        """standard hello response. white page with 200 code"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        # Send the html message
        self.wfile.write("Hello World !".encode())

    def do_GET(self):
        """
            self.path is the command the client wants to execute

            function_handler is a dictionary that contains {url : function responds to the command}
        """
        function_handler = {'/': self.hello,
                            '/get_info': self.info,
                            '/get_iwconfig': self.iwconfig,
                            '/get_config': self.get_config,
                            '/get_power': self.get_power,
                            '/set_power': self.set_power,
                            '/set_channel': self.set_channel,
                            '/get_stations': self.get_stations,
                            '/get_num_stations': self.get_num_stations,
                            '/get_features': self.get_features,
                            '/get_ifconfig': self.ifconfig,
                            '/get_xmit': self.xmit,
                            '/get_survey': self.get_survey,
                            '/get_scan': self.get_scan,
                            '/get_scan_mac': self.get_scan_mac,
                            '/get_mos_client': self.get_mos_client,
                            '/get_mos_ap': self.get_mos_ap,
                            '/get_mos_hybrid': self.get_mos_hybrid,
                            }
        LOG.info("received {} from {}".format(self.requestline, self.address_string()))
        LOG.debug('path: {}'.format(self.path))

        cmd = urllib.parse.urlparse(self.path).path
        LOG.debug('cmd : {}'.format(cmd))

        """Handler for the GET requests"""
        func = function_handler.get(cmd, self.send_error)
        func()
        return

    # ********************************************************
    #
    #  this is specific to the QoS experiments (Marcos, Gilson, Henrique)
    #
    # ********************************************************
    def fill_feature_results(self, survey, station, k, stations, iface):
        """ function that returns the features of a station.
            @param survey: data from iw survey dump
            @param station: the station data selected from the result of "iw station dump"
            @param k: the k-th value of the survey
            @param stations: data from iw station dump
            @param iface: wireless interface name
        """
        results = {'num_stations': len(stations),
                   'tx_power': get_power(interface=iface),
                   'cat': survey[k].get('channel active time', ''),
                   'cbt': survey[k].get('channel busy time', ''),
                   'crt': survey[k].get('channel receive time', ''),
                   'ctt': survey[k].get('channel transmit time', ''),
                   'avg_signal': station['signal avg'],
                   'txf': station['tx failed'],
                   'txr': station['tx retries'],
                   'txp': station['tx packets'],
                   'txb': station['tx bytes'],
                   'rxdrop': station['rx drop misc'],
                   'rxb': station['rx bytes'],
                   'rxp': station['rx packets'],
                   'tx_bitrate': station['tx bitrate'],
                   'rx_bitrate': station['rx bitrate'],
                   }
        return results

    def get_features(self):
        """ process /get_features

            here we collect all features necessary to train the QoS predictor

            @return: dictionary
                {'54:e6:fc:da:ff:34': {'tx_bitrate': 1.0, 'rx_bitrate': 1.0,
                                       'tx_power': 1.0, 'avg_signal': 54.0,
                                       'rxdrop': 16.0, 'rxb': 1232.0, 'rxp': 32.0,
                                       'txr': 0.0, 'txp': 3.0, 'txf': 0.0, 'txb': 487.0,
                                       'crt': 1073085286.0, 'cbt': 1163082876.0,
                                       'ctt': 60749755.0, 'cat': 3626867638.0,
                                       'num_stations': 1
                                       }
                }

        """
        iface = self.query.get('iface', ['wlan0'])[0]
        survey = get_iw_survey(interface=iface)
        k = [k for k in survey if survey[k].get('in use', False)][0]  # get only the channel in use

        stations = get_iw_stations(interface=iface)
        if len(self.query.get('mac', [''])[0]) == 0:
            # in case there is no parameter --mac
            result = stations
            for i in stations:
                try:
                    station = stations[i]
                    results = self.fill_feature_results(survey, station, k, stations, iface)
                    result[i] = results
                except KeyError:
                    self.send_error()
        else:
            # in case there is parameter --mac
            station_mac = self.query.get('mac', [''])[0]
            try:
                station = stations[station_mac]
                result = self.fill_feature_results(survey, station, k, stations, iface)
            except KeyError:
                self.send_error()
        try:
            self.send_dictionary(result)
        except KeyError:
            self.send_error()

    # ********************************************************
    #
    #  this is specific to the Video MOS experiments (Henrique's thesis)
    #
    # ********************************************************
    def get_mos_hybrid(self):
        """
            @return: [[timestamp, FR, frame_loss, SBR, PLR], ...]
        """
        iface = self.query.get('iface', ['wlan0'])[0]
        sta_mac_mapping_str = self.query.get('macs', [''])[0]
        sta_mac_mapping = json.loads(sta_mac_mapping_str.replace("'", "\""))
        # print(sta_mac_mapping)
        # get from memory
        data = ffox_memory.pop()
        LOG.debug(data)
        stations = list(set([d['host'] for d in data]))
        ret = []  # each line contains the data from the clients that compose the client's part of the HYBRID MOS
        for sta in stations:
            # get data to process
            sta_data = [d for d in data if d['host'] == sta and 'playing_time' in d]
            # print(sta_data)
            if len(sta_data) == 0:
                # get next data
                continue
            if sta in last_rt:
                # obtain the parameters
                last_data = last_rt[sta]
            else:
                last_data = sta_data.pop(0)  # get first to perform difference
            # get differences
            # * check if there is more than one entry for this station
            while len(sta_data) > 0:
                actual_data = sta_data.pop(0)
                # droppedFPS = actual_data['droppedFPS'] - last_data['droppedFPS']
                t1 = datetime.strptime(actual_data['timestamp'], '%Y%m%d%H%M%S')
                t0 = datetime.strptime(last_data['timestamp'], '%Y%m%d%H%M%S')
                interval = max((t1 - t0).seconds, 0)
                playing_time = actual_data['playing_time'] - last_data['playing_time']
                not_running = max(interval - playing_time, 0)

                FR = actual_data['reportedBitrate'] * playing_time / (playing_time + not_running)
                frame_loss = actual_data['droppedFPS'] - last_data['droppedFPS']

                ret.append([sta, actual_data['timestamp'], FR, frame_loss])
                last_data = actual_data
                break
            last_rt[sta] = last_data  # save for another iteration
        """
        * loss rate (PLR)
            packets = | rx_packets[t] - rx_packets[t-1] |
            PLR = rxdrop / (packets + rxdrop)

        * send bit rate (SBR): SBR = tx_bitrate / maximum tx_bitrate
        """
        stations = get_iw_stations(interface=iface)
        sta_macs = stations.keys()
        ret2 = dict()
        for k in sta_macs:
            sta = stations[k]
            h = sta_mac_mapping.get(k, '')
            ret2[h] = [sta['tx bitrate'] / MAXIMUM_TX_BITRATE,  # SBR
                       sta['rx drop misc'] / (sta['rx packets'] + sta['rx drop misc']),  # PLR
                       ]
        # join ret and ret2
        result = []  # contains the data to build the MOS
        for r in ret:
            try:
                result.append(r[1:] + ret2[r[0]])
            except KeyError:
                # do nothing
                LOG.debug("get_mos_hybrid: error using key {}".format(r[0]))
        LOG.debug(result)
        try:
            self.send_dictionary(result)
        except KeyError:
            self.send_error()

    def get_mos_ap(self):
        """ @return: [num_stations, BER, AMPDU, traffic_load]
                     needed to compute the MOS_AP
        """
        iface = self.query.get('iface', ['wlan0'])[0]
        #  number of competing stations: performance of the wireless network degrades withincreasing number of users,
        num_stations = len(get_iw_stations(interface=iface))

        # Bit Error Rate (BER): variation of the Bit Error Rate (BER) that can cause the MAC frame to be received with errors and trigger retransmissions that canimpact the overall performances of the system2.
        phy_iface = get_phy_with_wlan(interface=iface)
        r = get_xmit(phy_iface)
        tx_failed = np.sum([float(r[k]) for k in r if 'TX-Failed' in k])
        tx_pkts = np.sum([float(r[k]) for k in r if 'TX-Pkts-All' in k])
        # 'FER' = 'txf_detrend' / ('txf_detrend' + 'txp_detrend')
        denom = tx_failed + tx_pkts
        if denom != 0.0:
            FER = tx_failed / denom
        else:
            FER = 0
        BER = FER  # !!!!

        # frame aggregation: A-MPDU (MAC Protocol Data Unit) aggregation, allows many MAC frames to combine into one larger aggregated frame3.
        global last_ampdu
        curr_ampdu = np.sum([float(r[k]) for k in r if 'AMPDUs Completed' in k])
        if last_ampdu is None:
            AMPDU = 0
        else:
            AMPDU = curr_ampdu - last_ampdu
        last_ampdu = curr_ampdu

        # traffic load: percentage of traffic over the maximum throughput of the interface
        try:
            tx_bytes = float(get_ifconfig(interface=iface)['tx_bytes'])
        except ValueError:
            tx_bytes = 0
        global last_tx_bytes
        if last_tx_bytes is None:
            traffic_load = 0
        else:
            traffic_load = (tx_bytes - last_tx_bytes) / MAX_TX_BYTES_WIFI
        last_tx_bytes = tx_bytes

        result = [num_stations, BER, AMPDU, traffic_load]
        LOG.debug("num_stations:{} BER:{} AMPDU:{} traffic_load:{}".format(num_stations, BER, AMPDU, traffic_load))
        try:
            self.send_dictionary(result)
        except KeyError:
            self.send_error()

    def get_mos_client(self):
        """
            read from local memory is filled using an node.js server
            this server receives connections from the clients, and then stores
            the values in a local json file

            - r[t] = reportedBitrate in time [t] / max_bitrate
            - srt = not_running_time / (not_running_time + execution_time)
            - r[t-1] is obtained from a saved variable: self.last_rt[client_ip]

            @ return: [rt, rt_1, srt, actual mos, sta]
        """
        # get from memory
        data = ffox_memory.pop()
        LOG.debug(data)
        stations = list(set([d['host'] for d in data]))
        # from data, obtain: rt, rt_1, srt, sta
        ret = []  # each line contains (R_t, R_t1, SR) --> contains the data to build the MOS
        for sta in stations:
            # get data to process
            sta_data = [d for d in data if d['host'] == sta and 'playing_time' in d]
            if len(sta_data) == 0:
                # get next data
                continue
            if sta in last_rt:
                # obtain the parameters
                last_data = last_rt[sta]
            else:
                last_data = sta_data.pop(0)  # get first to perform difference
            # get differences
            # * check if there is more than one entry for this station
            while len(sta_data) > 0:
                actual_data = sta_data.pop(0)
                # droppedFPS = actual_data['droppedFPS'] - last_data['droppedFPS']
                t1 = datetime.strptime(actual_data['timestamp'], '%Y%m%d%H%M%S')
                t0 = datetime.strptime(last_data['timestamp'], '%Y%m%d%H%M%S')
                interval = (t1 - t0).seconds
                if interval > 0:
                    playing_time = actual_data['playing_time'] - last_data['playing_time']
                    not_running = max(interval - playing_time, 0)
                    srt = not_running / interval
                else:
                    srt = 0
                rt = actual_data.get('reportedBitrate', 0) / MAX_REPORTED_BITRATE
                rt_1 = last_data.get('reportedBitrate', rt) / MAX_REPORTED_BITRATE
                # print([rt, rt_1, srt])
                ret.append([rt, rt_1, srt, actual_data.get('mos', 1), sta])
                last_data = actual_data
                break

            last_rt[sta] = last_data  # save for another iteration
        LOG.debug(ret)
        try:
            self.send_dictionary(ret)
        except KeyError:
            self.send_error()


def run(port=8080):
    try:
        """ Create a web server and define the handler to manage the
            incoming request
            @param port: number of the server port. Defaults to 8080
        """
        server = HTTPServer(('', port), myHandler)
        LOG.info('Started httpserver on port {} to command Wi-Fi'.format(port))

        """Wait forever for incoming htto requests"""
        server.serve_forever()

    except KeyboardInterrupt:
        print('Ctrl-C received, shutting down the web server')
        server.socket.close()
        # stops the other server if the execution ever reaches this point
        if httpd is not None:
            httpd.socket.close()


def collect(port):
    """ creates an HTTP server that receives POST requests from the client
        save the BODY as JSON in a file

        @param port: number of the server port. Required.
    """
    server_address = ('', port)
    LOG.info('Starting httpd @ {}... for the firefox clients'.format(port))
    global httpd
    httpd = HTTPServer(server_address, SrvPosts)
    try:
        httpd.serve_forever()
    except ValueError:
        pass


if __name__ == "__main__":
    # check if is root
    if os.geteuid() != 0:
        print("User is not root.")
        print("Run script with sudo")
    else:
        parser = argparse.ArgumentParser(description='Receive commands to the AP.')
        parser.add_argument('--port', type=int, default=8080, help='Set the server port')
        parser.add_argument('--debug', action='store_true', help='set logging level to debug')

        parser.add_argument('--collect-firefox-data', action='store_true', help='creates a local server that receives POSTs from the web clients')
        parser.add_argument('--port-firefox', type=int, default=8081, help='Set the server port to collect data from the firefox client')
        args = parser.parse_args()

        if args.debug:
            logging.basicConfig(level=logging.DEBUG)
            LOG.setLevel(logging.DEBUG)
            LOG.info("Debug activated")

        if args.collect_firefox_data:
            # create thread to receive POSTs from the clients containing
            t = Thread(target=collect, args=(args.port_firefox, ))
            t.start()

        # run server forever
        run(args.port)
