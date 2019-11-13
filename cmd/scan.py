#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    convert the output of iw dev station dump into a dictionary

"""
import pickle


cmds = ['TSF', 'freq', 'beacon interval', 'capability', 'signal', 'last seen', 'SSID',
        'Supported rates', 'DS Parameter set', 'TIM', 'Country', 'Environment', 'Channels ',
        'station count', 'channel utilisation', 'available admission capacity', 'ERP',
        ]

cmds_sub = ['RSN', 'WMM', 'BSS Load', 'HT operation', 'Overlapping BSS scan params']


def find_in_cmd(line):
    """ searches the line against the text in `cmds`
        returns the data in a simple dictionary
    """
    ret = {}
    for cmd in cmds:
        p = line.find(cmd)
        if p >= 0:
            # item found
            item = line[p + len(cmd.strip()) + 1:].strip()
            item = item.split('\t')[0]
            ret.update({cmd: item})
    return ret


def get_subitems(_l, lines):
    r = {}
    i = 0
    _first = True
    while _first or _l.find('\t\t') == 0:
        _first = False
        if len(_l) > 0 and _l.find('*') > 0:
            p = _l.find('*')
            item = _l[p + 1:].strip()
            p = item.find(':')
            k = item[:p].strip()
            v = item[p + 1:].strip()
            r.update({k: v})
        _l = lines[i]
        i += 1
    # remove processed lines
    for j in range(i):
        lines.pop(0)
    return r


def decode_scan(data):
    """ decodes all the information returned by `scan dump`
        TODO: finish all fields

        @param data: the output of scan dump
        @return: dictionary containing the data
    """
    lines = data.split('\n')
    ret = dict()
    mac = None
    while len(lines) > 0:
        _l = lines.pop(0)
        if _l.find('BSS') == 0:
            mac = _l.split()[1].split('(')[0]
            iface = _l.split('on')[1].strip()
            ret[mac] = {'iface': iface}
        elif mac is not None:
            found = False
            for cmd in cmds_sub:
                if cmd in _l:
                    r = get_subitems(_l, lines)
                    # update result
                    ret[mac][cmd] = r
                    found = True  # skip the next process
            if not found:
                e = find_in_cmd(_l)
                ret[mac].update(e)

    return ret


def decode_scan_mac(data):
    """ get the list of APs in range

        @param data: the output of scan dump
        @return: list with the macs detected
    """
    macs = []
    lines = data.split('\n')
    while len(lines) > 0:
        _l = lines.pop(0)
        if _l.find('BSS') == 0:
            mac = _l.split()[1].split('(')[0]
            macs.append(mac)
    return macs


def decode_scan_basic(data):
    """ get the list of APs in range

        @param data: the output of scan dump
        @return: list with the macs detected
    """
    macs = dict()
    lines = data.split('\n')
    while len(lines) > 0:
        _l = lines.pop(0)
        if _l.find('BSS') == 0:
            mac = _l.split()[1].split('(')[0]
            macs[mac] = dict()
            i = 0
            while lines[i].find('BSS') < 0:
                if 'freq' in lines[i]:
                    macs[mac]['freq'] = int(lines[i].split(':')[1].strip())
                elif 'signal' in lines[i]:
                    macs[mac]['signal'] = float(lines[i].split(':')[1].strip().split()[0])
                elif 'beacon interval' in lines[i]:
                    macs[mac]['beacon interval'] = int(lines[i].split(':')[1].strip().split()[0])
                elif 'last seen' in lines[i]:
                    macs[mac]['last seen'] = int(lines[i].split(':')[1].strip().split()[0])
                elif 'SSID' in lines[i]:
                    macs[mac]['SSID'] = lines[i].split(':')[1].strip()
                elif 'DS Parameter set: channel' in lines[i]:
                    macs[mac]['channel'] = lines[i].split('channel')[1].strip()
                elif 'TSF' in lines[i]:
                    macs[mac]['TSF'] = lines[i].split('(')[1].strip().split(')')[0]

                i += 1  # next line
    return macs


if __name__ == '__main__':
    data = pickle.load(open('teste.p', 'rb'))
    ret = decode_scan(data)
    print(ret)
