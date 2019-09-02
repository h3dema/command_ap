#!/usr/bin/python3
# -*- coding: utf-8 -*-


"""
{'chunkData[resolution][]': '768',
'chunkData[start]': '32',
'chunkData[filename]': '7-16.video',
'chunkData[index]': '16',
'chunkData[quality]': '6',
'chunkData[endFragment]': 'true',
'chunkData[bandwidth]': '976342',
'chunkData[segmentType]': 'MediaSegment',
'playing[quality]': '6',
'playing[time]': '31.607175',
'playing[paused]': 'false',
'chunkData[representationId]': '7',
'chunkData[end]': '34',
'chunkData[codec]': 'video/mp4;codecs="avc3.64000C"'}

'index': 6,
'latency': {'avg': 0.04, 'low': 0.08, 'high': 0.06},
'droppedFPS': 15,
'maxIndex': 19,
'reportedBitrate': 976,
'calculatedBitrate': 810,
'video_ratio': {'avg': 11.63, 'low': 17.24, 'high': 13.63},
'bufferLevel': 2.4,
'download': {'avg': 0.12, 'low': 0.17, 'high': 0.15},

"""
import logging
import datetime
import threading

import numpy as np

from http.server import BaseHTTPRequestHandler
import urllib.parse


LOG = logging.getLogger('SERVER_FFOX')


def decode3field(x):
    ret = dict()
    vs = x.split('|')
    for k, v in zip(['avg', 'high', 'low'], vs):
        ret[k] = float(v.strip())
    return ret


def decodeInt(x):
    try:
        return int(x)
    except ValueError:
        return np.nan


funcs = {'droppedFPS': lambda x: decodeInt(x),
         'index': lambda x: decodeInt(x),
         'maxIndex': lambda x: decodeInt(x),
         'chunkData[resolution][]': lambda x: decodeInt(x),
         'chunkData[start]': lambda x: decodeInt(x),
         'chunkData[index]': lambda x: decodeInt(x),
         'chunkData[quality]': lambda x: decodeInt(x),
         'chunkData[bandwidth]': lambda x: decodeInt(x),
         'chunkData[representationId]': lambda x: decodeInt(x),
         'playing[quality]': lambda x: decodeInt(x),
         'playing[time]': lambda x: float(x),
         'reportedBitrate': lambda x: int(x.split()[0]),
         'bufferLevel': lambda x: float(x.split()[0]),
         'calculatedBitrate': lambda x: int(x.split()[0]),
         'download': lambda x: decode3field(x),
         'video_ratio': lambda x: decode3field(x),
         'latency': lambda x: decode3field(x),
         }

map_ip_to_sta = {'192.168.0.11': 'cloud',
                 '192.168.0.12': 'storm',
                 '150.164.10.18': 'vpn',
                 }


class FirefoxDataMemory (object):
    def __init__(self):
        self.lock = threading.Lock()
        self.__data = []

    def push(self, data):
        self.lock.acquire()
        try:
            self.__data.append(data)
        finally:
            self.lock.release()

    def pop(self):
        ret = []
        self.lock.acquire()
        try:
            ret = self.__data
            self.__data = []
        finally:
            self.lock.release()
        return ret


# saves the data retrieved from clients
ffox_memory = FirefoxDataMemory()


class SrvPosts(BaseHTTPRequestHandler):
    """ receives posts from the client (firefox), and saves the data into a json file
    """
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_POST(self):
        # get the data, and save it into a JSON file
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length).decode('utf-8')
        q = urllib.parse.parse_qs(post_data)
        for k in q:
            q[k] = q[k][0]

        data = dict()
        for k in funcs:
            if k in q:
                if 'chunkData' in k:
                    kd = k.replace('chunkData[', '').replace(']', '')
                elif 'playing' in k:
                    kd = k.replace('[', '_').replace(']', '')
                else:
                    kd = k
                data[kd] = funcs[k](q[k])
        data['timestamp'] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        ip = self.client_address[0]
        data['host'] = ip if ip not in map_ip_to_sta else map_ip_to_sta[ip]
        # LOG.info(data)
        ffox_memory.push(data)
