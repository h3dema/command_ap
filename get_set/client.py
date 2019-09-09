#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    the server accepts requests from an http client.
    this module is uses to send commands to the AP, for testing purposes.


    Usage:
    python3 server.py [--port 8080]
"""
import argparse
import pickle
import http.client
import urllib.parse
import sys

""" used to assert the valid commands.
    does not cover all available commands.
    see serve.py
"""
valid_urls = ['/', '/test', '/get_info', '/get_power', '/set_power',
              '/get_features', '/get_iwconfig',
              '/get_stations',
              '/get_num_stations',
              ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send commands to the AP.')
    parser.add_argument('--server', type=str, default='localhost', help='Set the server address')
    parser.add_argument('--port', type=int, default=8080, help='Set the server port')
    parser.add_argument('--url', type=str, default='/', help='url specifies the command')
    parser.add_argument('--interface', type=str, default='wlan0', help='wireless interface at the remote device')
    parser.add_argument('--txpower', type=str, default=15, help='set txpower when used with /set_power')
    parser.add_argument('--mac', type=str, help='set station mac when used with /get_features')

    args = parser.parse_args()

    if args.url not in valid_urls:
        print("valid urls:", ", ".join(valid_urls))
        print(parser.print_help())
        sys.exit(0)

    conn = http.client.HTTPConnection(args.server, args.port)

    if args.url in ['/get_info', '/get_iwconfig',
                    '/get_power',
                    '/get_stations', '/get_num_stations',
                    ]:
        params = {'iface': args.interface}
        q = urllib.parse.urlencode(params)
        url = "{}?{}".format(args.url, q)
    elif args.url in ['/set_power']:
        params = {'iface': args.interface, 'new_power': args.txpower}
        q = urllib.parse.urlencode(params)
        url = "{}?{}".format(args.url, q)
    elif args.url in ['/get_features']:
        if args.mac is None:
            params = {'iface': args.interface}
        else:
            params = {'iface': args.interface, 'mac': args.mac}
        q = urllib.parse.urlencode(params)
        url = "{}?{}".format(args.url, q)
    else:
        url = args.url

    # print(url)
    conn.request(method='GET', url=url)
    resp = conn.getresponse()
    print("status", resp.status)
    if resp.status == 200:
            """decode dictionary"""
            try:
                data = pickle.loads(resp.read())
                print(data)
            # print("received", data.values())
            except:
                pass
