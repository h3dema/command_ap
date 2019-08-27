#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    convert the output of iw dev station dump into a dictionary

"""
import pickle


cmds = ['TSF', 'freq', 'beacon interval', 'capability', 'signal', 'last seen', 'SSID', 'Supported rates', 'DS Parameter set', 'TIM', 'Country',
        'Environment', 'Channels ',
        'station count', 'channel utilisation', 'available admission capacity', 'ERP',]

def find_in_cmd(line):
    for cmd in cmds:
        p = line.find(cmd)
        if p >= 0:
            # item found
            item = line[p+len(cmd.strip())+1:].strip()
            return {cmd: item}
    return {}

def decode_scan(data):
    lines = data.split('\n')
    ret = dict()
    mac = None
    for _l in data.split('\n'):
        if _l.find('BSS') == 0:
            mac = _l.split()[1].split('(')[0]
            iface = _l.split('on')[1].strip()
            ret[mac] = {'iface':iface}
        elif mac is not None:
            e = find_in_cmd(_l)
            ret[mac].update(e)
            if len(e) == 0:
                print(_l)

    return ret

def decode_scan_mac(data):
    """
        :return: list with the macs detected
    """
    macs = []
    for _l in data.split('\n'):
        if _l.find('BSS') == 0:
            mac = _l.split()[1].split('(')[0]
            macs.append(mac)
    return macs


if __name__ == '__main__':
    data = pickle.load(open('teste.p', 'rb'))
    ret = decode_scan(data)
    print(ret)