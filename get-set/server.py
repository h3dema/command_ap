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

    def do_nothing(self):
        self.send_response(404)  # Not found
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        # Send the html message
        self.wfile.write("".encode())

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
        if new_power > 0:
            set_power(interface=iface, new_power=new_power)
        self.send_dictionary({'txpower': new_power})

    def hello(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        # Send the html message
        self.wfile.write("Hello World !".encode())

    def test(self):
        # Send the html message
        d = {'a': 1, 'b': 10}  # message
        self.send_dictionary(d)

    def do_GET(self):
        """
            self.path is the command the client wants to execute

            function_handler is a dictionary that contains {url : function responds to the command}
        """
        function_handler = {'/': self.hello,
                            '/test': self.test,
                            '/info': self.info,
                            '/iwconfig': self.iwconfig,
                            '/get_power': self.get_power,
                            '/set_power': self.set_power,
                            }

        print("received", self.requestline, 'from', self.address_string())
        print('path', self.path)

        cmd = urllib.parse.urlparse(self.path).path
        print(cmd)

        """Handler for the GET requests"""
        func = function_handler.get(cmd, self.do_nothing)
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

    run(args.port)

