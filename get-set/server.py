#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
    server that accepts requests from an http client
    used to send commands to the AP


    Usage from command line:
    -------------------

    python3 server.py [--port 8080]


    Usage from program:
    -------------------

    import server
    server.run(port)
"""
import argparse
import pickle
import os
import json
import logging
import urllib.parse
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

# add path to sys, in order to access the commands
from ..cmd.command_ap import get_iw_info, get_power, set_power, get_iwconfig_info
from ..cmd.command_ap import get_survey, get_iw_stations
from ..cmd.command_ap import get_xmit, get_ifconfig
from ..cmd.command_ap import get_scan


LOG = logging.getLogger('REST_SERVER')
PORT_NUMBER = 8080


class myHandler(BaseHTTPRequestHandler):
    """"This class will handles any incoming request from the browser
    """
    def __init__(self, request, client_address, server):
        super.__init__(request, client_address, server)

        self.last_rt = dict()  # used in get_mos_client()

    @property
    def query(self):
        q = urllib.parse.urlparse(self.path).query
        return urllib.parse.parse_qs(q)

    def send_error(self):
        self.send_response(404)  # Not found
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        # Send the html message
        self.wfile.write("Command unknown".encode())

    def send_dictionary(self, d):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        msg = pickle.dumps(d, protocol=pickle.HIGHEST_PROTOCOL)
        self.wfile.write(msg)

    def info(self):
        """ process /get_info

        :return:
        """
        iface = self.query.get('iface', [''])[0]
        info = get_iw_info(interface=iface)
        self.send_dictionary(info)

    def iwconfig(self):
        """ process /get_iwconfig

        :return:
        """
        iface = self.query.get('iface', [''])[0]
        r = get_iwconfig_info(interface=iface)
        self.send_dictionary(r)

    def ifconfig(self):
        """ process /get_ifconfig

        :return:
        """
        iface = self.query.get('iface', [''])[0]
        r = get_ifconfig(interface=iface)
        self.send_dictionary(r)

    def get_power(self):
        """ process /get_power

        :return: the tx power of iface
        """
        iface = self.query.get('iface', [''])[0]
        pwr = get_power(interface=iface)
        self.send_dictionary({'txpower': pwr})

    def set_power(self):
        """ process /set_power

        :return: set the tx power of iface to new_power
        """
        iface = self.query.get('iface', [''])[0]
        new_power = self.query.get('new_power', [-1])[0]
        if len(new_power) > 0:
            set_power(interface=iface, new_power=new_power)
        self.send_dictionary({'txpower': new_power})

    def xmit(self):
        """ process /get_xmit

        :return:
        """
        phy_iface = self.query.get('iface', [''])[0]
        r = get_xmit(phy_iface)
        self.send_dictionary(r)

    def fill_feature_results(self, survey, station, k, stations, iface):
        """ function that returns the features of a station.
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

    def get_stations(self):
        """ process /num_stations

        :return:
        """
        iface = self.query.get('iface', [''])[0]
        stations = get_iw_stations(interface=iface)
        self.send_dictionary(stations)

    def get_num_stations(self):
        """ process /get_num_stations

        :return:
        """
        iface = self.query.get('iface', [''])[0]
        stations = get_iw_stations(interface=iface)
        self.send_dictionary({'num_stations': len(stations)})

    def get_features(self):
        """ process /get_features

            here we collect all features necessary to train the QoS predictor
        """
        iface = self.query.get('iface', [''])[0]
        survey = get_survey(interface=iface)
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

    def get_mos_hybrid(self, database_filename='clients.json'):
        pass
        # each line: (fr, sbr, plr)

    def get_mos_client(self, database_filename='clients.json'):
        """
            read a local file that is filled using an node.js server
            this server receives connections from the clients, and then stores
            the values in a local json file
        """
        # rename database_file
        to_send = database_filename + '.send'
        os.rename(database_filename, to_send)
        # recreate it
        os.system('touch {}'.format(database_filename))
        # read json to send
        with open(to_send, 'r') as f:
            data = json.load(f)
        data_print = json.dumps(data, indent=4)
        LOG.debug(data_print)
        # from data, obtain:
        # * r[t] = reportedBitrate in time [t] / max_bitrate
        # * srt = not_running_time / (not_running_time + execution_time)
        # r[t-1] is obtained from a saved variable: self.last_rt[client_ip]
        ret = []  # each line contains (R_t, R_t1, SR)
        for d in data:
            pass
        try:
            self.send_dictionary(ret)
        except KeyError:
            self.send_error()
        # delete the json
        os.remove(to_send)

    def get_scan(self):
        """ return the result from iw scan dump
        """
        iface = self.query.get('iface', [''])[0]
        aps = get_scan(interface=iface)
        self.send_dictionary(aps)

    def hello(self):
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
                            '/get_power': self.get_power,
                            '/get_stations': self.get_stations,
                            '/num_stations': self.get_num_stations,
                            '/set_power': self.set_power,
                            '/get_features': self.get_features,
                            '/get_ifconfig': self.ifconfig,
                            '/get_xmit': self.xmit,
                            '/get_mos_client': self.get_mos_client,
                            '/get_mos_hybrid': self.get_mos_hybrid,
                            '/get_scan': self.get_scan,
                            }

        LOG.info("received {} from {}".format(self.requestline, self.address_string()))
        LOG.info('path: {}'.format(self.path))

        cmd = urllib.parse.urlparse(self.path).path
        LOG.info('cmd : {}'.format(cmd))

        """Handler for the GET requests"""
        func = function_handler.get(cmd, self.send_error)
        func()
        return


def run(port=8080):
    try:
        """Create a web server and define the handler to manage the
            incoming request"""
        server = HTTPServer(('', port), myHandler)
        LOG.info('Started httpserver on port {}'.format(port))

        """Wait forever for incoming htto requests"""
        server.serve_forever()

    except KeyboardInterrupt:
        print('Ctrl-C received, shutting down the web server')
        server.socket.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Receive commands to the AP.')
    parser.add_argument('--port', type=int, default=8080, help='Set the server port')
    args = parser.parse_args()

    run(args.port)
