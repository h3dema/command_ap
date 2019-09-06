#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    convert the output of iw dev station dump into a dictionary

"""
import re


def decode_iw_station(data):
    """ return the data from "iw dev station dump"

    @param data: output from "iw dev station dump"
    @return:
    """
    result = dict()
    station = None
    for _l in data:
        if 'Station' in _l:
            station = _l.split()[1]
            result[station] = dict()
        elif station is not None and len(_l.strip()) > 0:
            _l = _l.split(':')
            v = _l[1].strip().split()[0]
            f = re.findall(r"[-+]?\d*\.\d+|\d+", v)
            if len(f) > 0:
                v = f[0]
            try:
                v = float(v)
            except ValueError:
                pass
            result[station][_l[0]] = v
    return result


def decode_hostapd_status(data):
    """ decodes "hostapd_cli status"'s output

    @param data: output from hostapd_cli status
    @return: dictionary containing
        {olbc_ht : 1
         cac_time_left_seconds : N/A
         num_sta_no_short_slot_time : 0
         olbc : 0
         num_sta_non_erp : 0
         ht_op_mode : 0x15
         state : ENABLED
         num_sta_ht40_intolerant : 0
         channel : 6
         bssid[0] : b0:aa:ab:ab:ac:11
         ieee80211n : 1
         cac_time_seconds : 0
         num_sta[0] : 2
         ieee80211ac : 0
         phy : phy0
         num_sta_ht_no_gf : 1
         freq : 2437
         num_sta_ht_20_mhz : 2
         num_sta_no_short_preamble : 0
         secondary_channel : 0
         ssid[0] : ethanolQL1
         num_sta_no_ht : 0
         bss[0] : wlan0
        }

    """
    lines = data.split('\n')
    ret = dict([v for v in [a.split("=") for a in lines] if len(v) == 2])
    for k in ret:
        try:
            ret[k] = int(ret[k])
        except ValueError:
            pass
    return ret


def is_mac(s):
    """ verifies if 's' contains a MAC address

        @return: the mac address found or None
        @rtype: str
    """
    try:
        mac = re.search(r'([0-9A-F]{2}[:-]){5}([0-9A-F]{2})', s, re.I).group()
        return mac
    except AttributeError:
        return None


def decode_hostapd_station(data):
    """

    @param data: output from hostapd_cli all_sta
    @return: dictionary of dictionary
         {station1_mac: {'dot11RSNAStatsSelectedPairwiseCipher': '00-0f-ac-4',
                         'rx_packets': '164',
                         'dot11RSNAStatsTKIPLocalMICFailures': '0',
                         'rx_bytes': '5420',
                         'inactive_msec': '11828',
                         'connected_time': '3402',
                         'hostapdWPAPTKState': '11',
                         'tx_bytes': '1340',
                         'dot11RSNAStatsVersion': '1',
                         'tx_packets': '10',
                         'hostapdWPAPTKGroupState': '0',
                         'dot11RSNAStatsTKIPRemoteMICFailures': '0'},
         }
    """
    result = dict()
    lines = data.split('\n')
    mac = None
    for _l in lines:
        _mac = is_mac(_l)
        if _mac is None and mac is None:
            continue  # skip line
        else:
            if _mac is not None:
                # found a new station
                mac = _mac
                result[mac] = []
            else:
                result[mac].append(_l.split('='))
    for k in result:
        try:
            result[k] = dict([v for v in result[k] if len(v) == 2])
        except ValueError:
            result[k] = None
    return result
