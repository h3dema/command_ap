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
import glob

from .xmit import decode_xmit
from .ifconfig import decode_ifconfig
from .iwconfig import decode_iwconfig
from .station import decode_iw_station, decode_hostapd_status, decode_hostapd_station
from .survey import decode_survey
from .scan import decode_scan


valid_frequencies = [2412 + i * 5 for i in range(13)]
__HOSTAPD_CLI = "hostapd_cli"
__DEFAULT_HOSTAPD_CLI_PATH = '/usr/sbin/'
__DEFAULT_IW_PATH = '/sbin/'
__DEFAULT_IWCONFIG_PATH = '/sbin'
__PATH_IFCONFIG='/sbin'


def get_xmit(phy_iface='phy0'):
    # TODO: find if it is ath9k, ath10k....
    path_to_phy = os.path.join('/sys/kernel/debug/ieee80211', phy_iface)
    try:
        dir_athk = glob.glob(os.path.join(path_to_phy, 'ath*k'))[0]
    except IndexError:
        return dict()  # error, didn't find ath9k or ath10k
    path_to_xmit = os.path.join(path_to_phy, dir_athk, 'xmit')
    ret = decode_xmit(path_to_xmit)
    return ret


def get_ifconfig(interface, path_ifconfig=__PATH_IFCONFIG):
    cmd = "{} {}".format(os.path.join(path_ifconfig, 'ifconfig'), interface)
    with os.popen(cmd) as p:
        ret = decode_ifconfig(p.readlines())
    return ret


def get_iw_stations(interface, path_iw=__DEFAULT_IW_PATH):
    cmd = "{} dev {} station dump".format(os.path.join(path_iw, 'iw'), interface)
    with os.popen(cmd) as p:
        data = p.read().replace('\t', '').split('\n')
    result = decode_iw_station(data)
    return result


def get_status(path_hostapd_cli=__DEFAULT_HOSTAPD_CLI_PATH):
    """ get information from hostapd_cli status

        todo: what if the interface has multiple SSIDs ???
    """
    cmd = "{} status".format(os.path.join(path_hostapd_cli, 'hostapd_cli'))
    with os.popen(cmd) as p:
        data = p.read()
    ret = decode_hostapd_status(data)
    return ret


def change_channel(new_channel, count=1, path_hostapd_cli=__DEFAULT_HOSTAPD_CLI_PATH):
    assert new_channel > 0 and new_channel <= len(valid_frequencies), "{} not in valid channels".format(new_channel)
    frequency = valid_frequencies[new_channel - 1]
    params = "chan_switch {} {}".format(count, frequency)
    cmd = "{} {}".format(os.path.join(path_hostapd_cli, __HOSTAPD_CLI), params)
    with os.popen(cmd) as p:
        ret = p.read().find('OK') >= 0
    return ret


def get_stations(path_hostapd_cli=__DEFAULT_HOSTAPD_CLI_PATH):
    """ returns information about all connected stations

        :param path_hostapd_cli: path to hostapd_cli
        :return dictionary of dictionary
    """
    cmd = "{} all_sta".format(os.path.join(path_hostapd_cli, __HOSTAPD_CLI))
    with os.popen(cmd) as p:
        data = p.read()
    result = decode_hostapd_station(data)
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


def get_iwconfig_info(interface, path_iwconfig=__DEFAULT_IWCONFIG_PATH):
    """ NOTE: this method only supports (tested) two modes = Managed and Master
    """
    cmd = "{} {}".format(os.path.join(path_iwconfig, 'iwconfig'), interface)
    with os.popen(cmd) as p:
        result = {'interface': interface}
        data = p.read()
        r = decode_iwconfig(data)
        result.update(r)
    return result


def get_power(interface, path_iw=__DEFAULT_IW_PATH, path_iwconfig=__DEFAULT_IWCONFIG_PATH):
    """ get the power in the interface (from a station or AP)

        :param interface: interface to change
        :param path_iw: path to iw
    """
    ret = get_iw_info(interface, path_iw)
    txpower = ret.get('txpower', None)
    if txpower is None:
        ret = get_iwconfig_info(interface, path_iwconfig)
        txpower = ret.get('Tx Power', None)
    f = re.findall(r"[-+]?\d*\.\d+|\d+", txpower)
    if len(f) > 0:
        v = f[0]
        try:
            txpower = float(v)
        except ValueError:
            pass  # nothing to do
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
    else:
        return -1  # error
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
        result = p.read().split('\n')
    result.pop(0)  # remove first line (blank line)
    result = dict([w for w in [v.split('=') for v in ret] if len(w) == 2])
    return result


def get_survey(interface, path_iw=__DEFAULT_IW_PATH):
    """ command  dev <devname> survey dump

        :param interface: interface to change
        :param path_iw: path to iw

        :return decoded information from survey
    """
    cmd = "{} dev {} survey dump".format(os.path.join(path_iw, 'iw'), interface)
    with os.popen(cmd) as p:
        data = p.read()
    result = decode_survey(data)
    return result


def get_scan(interface, path_iw=__DEFAULT_IW_PATH):
    """ command  dev <devname> scan dump

        :param interface: interface to change
        :param path_iw: path to iw

        :return decoded information from scan dump
    """
    cmd = "{} dev {} scan dump".format(os.path.join(path_iw, 'iw'), interface)
    with os.popen(cmd) as p:
        data = p.read()
    result = decode_scan(data)
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

    parser.add_argument('--iw-stations', action='store_true', help='get stations using iw command')

    parser.add_argument('--power', type=str, default=None, help='set new power in dBm')

    parser.add_argument('--disassociate', type=str, default=None, help='disassociate station')
    args = parser.parse_args()

    if args.iw_stations:
        print(get_iw_stations(args.iface))

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
        print("iwconfig", ret)
