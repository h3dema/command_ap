#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#
#
# Help library in python that access hostapd_cli and iw
# to get information about the AP, or to set basic configuration
#
#
#
#
import os
import argparse
import re


valid_frequency = [2412 + i * 5 for i in range(13)]
__HOSTAPD_CLI = "hostapd_cli"
__DEFAULT_HOSTAPD_CLI_PATH = '/usr/sbin/'
__DEFAULT_IW_PATH = '/sbin/'
__DEFAULT_IWCONFIG_PATH = '/sbin'


def get_status(path_hostapd_cli=__DEFAULT_HOSTAPD_CLI_PATH):
    """ get information from hostapd_cli

        todo: what if the interface has multiple SSIDs ???

        :return dictionary containing
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
    cmd = "{} status".format(os.path.join(path_hostapd_cli, 'hostapd_cli'))
    with os.popen(cmd) as p:
        lines = p.read().split('\n')
    ret = dict([v for v in [a.split("=") for a in lines] if len(v) == 2])
    for k in ret:
        try:
            ret[k] = int(ret[k])
        except ValueError:
            pass
    return ret


def change_channel(new_channel, count=1, path_hostapd_cli=__DEFAULT_HOSTAPD_CLI_PATH):
    assert new_channel > 0 and new_channel <= len(valid_frequency), "{} not in valid channels".format(new_channel)
    frequency = valid_frequency[new_channel - 1]
    params = "chan_switch {} {}".format(count, frequency)
    cmd = "{} {}".format(os.path.join(path_hostapd_cli, __HOSTAPD_CLI), params)
    with os.popen(cmd) as p:
        ret = p.read().find('OK') >= 0
    return ret


def is_mac(s):
    """ verifies if s contains a MAC address

        :return the mac address found or None
    """
    try:
        mac = re.search(r'([0-9A-F]{2}[:-]){5}([0-9A-F]{2})', s, re.I).group()
        return mac
    except AttributeError:
        return None


def get_stations(path_hostapd_cli=__DEFAULT_HOSTAPD_CLI_PATH):
    """ returns information about all connected stations

        :param path_hostapd_cli: path to hostapd_cli
        :return dictionary of dictionary
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
    cmd = "{} all_sta".format(os.path.join(path_hostapd_cli, __HOSTAPD_CLI))
    result = {}
    with os.popen(cmd) as p:
        ret = p.read().split('\n')
    mac = None
    for _l in ret:
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


def get_iw_info(interface, path_iw=__DEFAULT_IW_PATH):
    cmd = "{} dev {} info".format(os.path.join(path_iw, 'iw'), interface)
    with os.popen(cmd) as p:
        ret = p.read().replace('\t', '').split('\n')
        result = []
        for i in range(len(ret)):
            if 'channel' in ret[i]:
                _l = ret[i].replace(' MHz', 'MHz').replace(':', '').replace('(', '').replace(')', '').split()
                try:
                    result.append(_l[:2])
                    result.append(['frequency', _l[2]])
                    result.append(_l[3:5])
                    result.append(_l[5:7])
                except IndexError:
                    pass  # nothing to do
            elif 'txpower' in ret[i]:
                _l = ret[i].split()
                result.append([_l[0], '{} {}'.format(_l[1], _l[2])])
            else:
                result.append(ret[i].split())
        result = dict([v for v in result if len(v) == 2])
    return result


def grab_first(x, k, type=None):
    """ helper function to decode iwconfig"""
    v = x.split(k)[1].split()[0]
    if type is not None:
        try:
            v = type(v)
        except ValueError:
            pass  # just keep the same value
    return v


cmds_iwconfig = {'IEEE': lambda x: grab_first(x, 'IEEE'),
                 'ESSID': lambda x: grab_first(x, 'ESSID:'),
                 'Mode': lambda x: grab_first(x, 'Mode:'),
                 'Frequency': lambda x: grab_first(x, 'Frequency:', float),
                 'AP': lambda x: grab_first(x, 'Access Point: '),
                 'Bit Rate': lambda x: grab_first(x, 'Bit Rate=', int),
                 'Tx Power': lambda x: grab_first(x, 'Tx-Power=', int),
                 'Retry short limit': lambda x: grab_first(x, 'Retry short limit:', int),
                 'RTS thr': lambda x: grab_first(x, 'RTS thr:'),
                 'Fragment thr': lambda x: grab_first(x, 'Fragment thr:'),
                 'Power Management': lambda x: grab_first(x, 'Power Management:'),
                 'Link Quality': lambda x: grab_first(x, 'Link Quality='),
                 'Signal level': lambda x: grab_first(x, 'Signal level=', int),
                 'Rx invalid nwid': lambda x: grab_first(x, 'Rx invalid nwid:', int),
                 'Rx invalid crypt': lambda x: grab_first(x, 'Rx invalid crypt:', int),
                 'Rx invalid frag': lambda x: grab_first(x, 'Rx invalid frag:', int),
                 'Tx excessive retries': lambda x: grab_first(x, 'Tx excessive retries:', int),
                 'Invalid misc': lambda x: grab_first(x, 'Invalid misc:', int),
                 'Missed beacon': lambda x: grab_first(x, 'Missed beacon:', int),
                 }


def get_iwconfig_info(interface, path_iwconfig=__DEFAULT_IWCONFIG_PATH):
    """ NOTE: this method only supports two modes = Managed and Master
    """
    cmd = "{} {}".format(os.path.join(path_iwconfig, 'iwconfig'), interface)
    with os.popen(cmd) as p:
        ret = p.read().replace('\t', '').split('\n')
        result = {'interface': interface}
        for line in ret:
            for k in cmds_iwconfig:
                if k in line:
                    f = cmds_iwconfig[k]
                    x = f(line)
                    result[k] = x
    return result


def get_power(interface, path_iw=__DEFAULT_IW_PATH, path_iwconfig=__DEFAULT_IWCONFIG_PATH):
    """ get the power in the interface (from a station or AP)

        :param interface: interface to change
        :param path_iw: path to iw
    """
    ret = get_iw_info(interface, path_iw)
    if ret.get('type', '') == 'AP':
        ret = get_iwconfig_info(interface, path_iwconfig)
        txpower = ret.get('Tx Power', None)
    else:
        txpower = ret.get('txpower', None)
    return txpower


def set_power(interface, new_power, path_iw=__DEFAULT_IW_PATH):
    """ command dev <devname> set txpower <auto|fixed|limit> [<tx power in mBm>]
        NOTE: this module needs to run as superuser to set the power

        :param interface: interface to change
        :param new_power: can be a string 'auto', or a number (int or float) that represents the new power in dBm
        :param path_iw: path to iw
    """
    iw_cmd = "{}".format(os.path.join(path_iw, 'iw'))
    if new_power == 'auto':
        cmd = "{} dev {} set txpower auto".format(iw_cmd, interface)
    elif isinstance(new_power, int) or isinstance(new_power, float):
        new_power = int(float(new_power) * 100)
        cmd = "{} dev {} set txpower fixed {}".format(iw_cmd, interface, new_power)
    with os.popen(cmd) as p:
        ret = p.read()
    return ret


def disassociate_sta(mac_sta, path_hostapd_cli=__DEFAULT_HOSTAPD_CLI_PATH):
    cmd = "{} disassociate {}".format(os.path.join(path_hostapd_cli, __HOSTAPD_CLI), mac_sta)
    with os.popen(cmd) as p:
        ret = p.read()
    return 'OK' in ret


def get_config(path_hostapd_cli=__DEFAULT_HOSTAPD_CLI_PATH):
    """
        :return dictionary {'ssid': 'ethanolQL1',
                            'bssid': 'b0:aa:ab:ab:ac:11',
                            'rsn_pairwise_cipher': 'CCMP',
                            'group_cipher': 'CCMP',
                            'key_mgmt': 'WPA-PSK',
                            'wpa': '2',
                            'wps_state': 'disabled'}
    """
    cmd = "{} get_config".format(os.path.join(path_hostapd_cli, __HOSTAPD_CLI))
    with os.popen(cmd) as p:
        ret = p.read().split('\n')
    ret.pop(0)
    ret = dict([w for w in [v.split('=') for v in ret] if len(w) == 2])
    return ret


def get_survey(interface, path_iw=__DEFAULT_IW_PATH):
    """ command  dev <devname> survey dump

        :param interface: interface to change
        :param path_iw: path to iw

        :return dictionary of dictionary
            {2432: {'noise': '-95 dBm',
                    'in use': True,
                    'channel transmit time': '713 ms',
                    'channel busy time': '9479 ms',
                    'channel active time': '54259 ms',
                    'channel receive time': '8279 ms'},
             2467: {},
             }
    """
    cmd = "{} dev {} survey dump".format(os.path.join(path_iw, 'iw'), interface)
    with os.popen(cmd) as p:
        ret = p.read().split('\n')
    result = dict()
    freq = None
    for _l in ret:
        if 'Survey data' in _l:
            continue  # skip this line
        if 'frequency' in _l:
            # new field
            freq = int(_l.replace('\t', ' ').split()[1])
            result[freq] = {'in use': True} if 'in use' in _l else dict()
            continue
        if freq is not None:
            _l = [v.strip() for v in _l.replace('\t', ' ').split(':')]
            try:
                result[freq][_l[0]] = _l[1]
            except IndexError:
                pass
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='get wifi info.')
    parser.add_argument('--verbose', action='store_true', help='verbose')

    parser.add_argument('--path-hostapd-cli', type=str, default=__DEFAULT_HOSTAPD_CLI_PATH, help='path to hostapd_cli')
    parser.add_argument('--path-iw', type=str, default=__DEFAULT_IW_PATH, help='path to iw')

    parser.add_argument('--iface', type=str, default='wlan0', help='interface to query')

    parser.add_argument('--info', action='store_true', help='show hostapd info')
    parser.add_argument('--iw', action='store_true', help='show hostapd info')
    parser.add_argument('--iwconfig', action='store_true', help='show iwconfig info')

    parser.add_argument('--increment-channel', action='store_true', help='increment the channel (cycle)')
    parser.add_argument('--channel', type=int, default=None, help='set the channel')

    parser.add_argument('--stations', action='store_true', help='show stations')
    parser.add_argument('--survey', action='store_true', help='survey channels')

    parser.add_argument('--power', type=str, default=None, help='set new power in dBm')

    parser.add_argument('--disassociate', type=str, default=None, help='disassociate station')
    args = parser.parse_args()

    status = get_status(args.path_hostapd_cli)
    if args.info:
        for k, v in status.items():
            print("{} : {}".format(k, v))

    if args.channel is not None:
        try:
            channel = int(args.channel)
            change_channel(channel, path_hostapd_cli=args.path_hostapd_cli)
        except ValueError:
            pass

    if args.increment_channel:
        channel = status.get('channel', 1)
        if args.verbose:
            print("curr channel: {}".format(channel))

        channel = (channel + 1) % 11
        if channel == 0:
            channel = 1

        if change_channel(channel, path_hostapd_cli=args.path_hostapd_cli):
            if args.verbose:
                print("new channel: {}".format(channel))
        elif args.verbose:
            print("error during channel change")

    if args.stations:
        stations = get_stations(path_hostapd_cli=args.path_hostapd_cli)
        if stations is not None:
            print('Num stations connected: {}'.format(len(stations)))
            for k in stations:
                print("Station MAC {}".format(k))
                for v in stations[k]:
                    print('\t{}: {}'.format(v, stations[k][v]))

    if args.iw:
        print(get_iw_info(args.iface, path_iw=args.path_iw))

    if args.power is not None:
        if args.power == 'auto':
            new_power = 'auto'
        else:
            try:
                new_power = float(args.power)
            except ValueError:
                new_power = None
        if new_power is not None:
            set_power(args.iface, new_power=new_power, path_iw=args.path_iw)
        if args.verbose:
            print('Power: {}'.format(get_power(interface=args.iface, path_iw=args.path_iw)))

    if args.disassociate is not None:
        disassociate_sta(args.disassociate)

    # print(get_config(path_hostapd_cli=args.path_hostapd_cli))

    if args.survey:
        ret = get_survey(args.iface)
        for k in ret:
            print("Channel: {}".format(k))
            for w in ret[k]:
                print('\t{}: {}'.format(w, ret[k][w]))


    if args.iwconfig:
        ret = get_iwconfig_info(args.iface)
        print(ret)
