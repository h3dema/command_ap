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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send commands to the AP.')
    parser.add_argument('--server', type=str, default='localhost', help='Set the server address')
    parser.add_argument('--port', type=int, default=8080, help='Set the server port')
    parser.add_argument('--url', type=str, default='/', help='url specifies the command')

    args = parser.parse_args()

    conn = http.client.HTTPConnection(args.server, args.port)
    conn.request(method='GET', url=args.url)
    resp = conn.getresponse()
    print("status", resp.status)
    if resp.status == 200 and args.url == '/test':
        """decode dictionary"""
        data = pickle.loads(resp.read())
        print("received", data)
