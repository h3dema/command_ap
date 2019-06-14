#!/usr/bin/python
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
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer


PORT_NUMBER = 8080


class myHandler(BaseHTTPRequestHandler):
    """"This class will handles any incoming request from the browser
    """
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
        iface = self.query.get('iface', [''])[0]
        info = get_iw_info(interface=iface)
        self.send_dictionary(info)

    def iwconfig(self):
        iface = self.query.get('iface', [''])[0]
        r = get_iwconfig_info(interface=iface)
        self.send_dictionary(r)

    def get_power(self):
        iface = self.query.get('iface', [''])[0]
        pwr = get_power(interface=iface)
        self.send_dictionary({'txpower': pwr})

    def set_power(self):
        iface = self.query.get('iface', [''])[0]
        new_power = self.query.get('new_power', [-1])[0]
        if len(new_power) > 0:
            set_power(interface=iface, new_power=new_power)
        self.send_dictionary({'txpower': new_power})




    def cal_features(self, survey, station, k, stations, iface):
        """ function to get feature of the stations.
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
        """ here we collect all features necessary to train the QoS predictor
        """
        iface = self.query.get('iface', [''])[0]
        survey = get_survey(interface=iface)
        k = [k for k in survey if survey[k].get('in use', False)][0]  # get only the channel in use

        stations = get_iw_stations(interface=iface)
        # in case there is no parameter --mac
        if len(self.query.get('mac', [''])[0]) == 0:
            result = stations
            for i in stations:
                try:
                    station = stations[i]
                    results = self.cal_features(survey, station, k, stations, iface)
                    result[i] = results
                except KeyError:
                    self.send_error() 
        # in case there is parameter --mac                    
        else:
            station_mac = self.query.get('mac', [''])[0]        
            try:
                station = stations[station_mac]
                result = self.cal_features(survey, station, k, stations, iface)
            except KeyError:
                self.send_error()
        try:
            self.send_dictionary(result)
        except KeyError:
            self.send_error()

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
                            '/info': self.info,
                            '/iwconfig': self.iwconfig,
                            '/get_power': self.get_power,
                            '/set_power': self.set_power,
                            '/get_features': self.get_features,
                            }

        print("received", self.requestline, 'from', self.address_string())
        print('path', self.path)

        cmd = urllib.parse.urlparse(self.path).path
        print(cmd)

        """Handler for the GET requests"""
        func = function_handler.get(cmd, self.send_error)
        func()
        return


def run(port):
    try:
        """Create a web server and define the handler to manage the
            incoming request"""
        server = HTTPServer(('', port), myHandler)
        print('Started httpserver on port ', port)

        """Wait forever for incoming htto requests"""
        server.serve_forever()

    except KeyboardInterrupt:
        print('Ctrl-C received, shutting down the web server')
        server.socket.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Receive commands to the AP.')
    parser.add_argument('--port', type=int, default=8080, help='Set the server port')
    args = parser.parse_args()

    # add path to sys, in order to access the commands
    sys.path.append('../cmd')
    from command_ap import get_iw_info, get_power, set_power, get_iwconfig_info
    from command_ap import get_survey, get_iw_stations

    run(args.port)

