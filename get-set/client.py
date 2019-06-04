#!/usr/bin/python
"""
    server that accepts requests from an http client
    used to send commands to the AP


    Usage:
    python3 server.py [--port 8080]
"""
import argparse
import http.client
import pickle
import urllib.parse


valid_urls = ['/', '/test', '/info', '/get_power', '/set_power', '/iwconfig']


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send commands to the AP.')
    parser.add_argument('--server', type=str, default='localhost', help='Set the server address')
    parser.add_argument('--port', type=int, default=8080, help='Set the server port')
    parser.add_argument('--url', type=str, default='/', help='url specifies the command')
    parser.add_argument('--interface', type=str, default='wlan0', help='wireless interface at the remote device')
    parser.add_argument('--txpower', type=int, default=15, help='set txpower when used with /set_power')

    args = parser.parse_args()
    conn = http.client.HTTPConnection(args.server, args.port)

    if args.url in ['/info', '/iwconfig', '/get_power']:
        params = {'iface': args.interface}
        q = urllib.parse.urlencode(params)
        url = "{}?{}".format(args.url, q)
    elif args.url in ['/set_power']:
        params = {'iface': args.interface, 'new_power': 1}
        q = urllib.parse.urlencode(params)
        url = "{}?{}".format(args.url, q)
    else:
        url = args.url
    conn.request(method='GET', url=url)
    resp = conn.getresponse()
    print("status", resp.status)
    if resp.status == 200:
        if args.url in ['/test', '/info', '/get_power', '/iwconfig']:
            """decode dictionary"""
            data = pickle.loads(resp.read())
            print("received", data)


