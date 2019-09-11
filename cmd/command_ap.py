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
import logging

from cmd.xmit import decode_xmit
from cmd.ifconfig import decode_ifconfig
from cmd.iwconfig import decode_iwconfig
from cmd.station import decode_iw_station, decode_hostapd_status, decode_hostapd_station
from cmd.survey import decode_survey
from cmd.scan import decode_scan, decode_scan_mac, decode_scan_basic


logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger('CMD')

valid_frequencies = [2412 + i * 5 for i in range(13)]
__HOSTAPD_CLI = "hostapd_cli"
__DEFAULT_HOSTAPD_CLI_PATH = '/usr/sbin/'
__DEFAULT_IW_PATH = '/sbin/'
__DEFAULT_IWCONFIG_PATH = '/sbin'
__PATH_IFCONFIG = '/sbin'


def get_xmit(phy_iface='phy0'):
    """ get data from the xmit file.
        looks for it in /sys/kernel/debug/ieee80211/ath*/xmit

        @return: the xmit fields
        @rtype: dict
    """
    # TODO: find if it is ath9k, ath10k....
    path_to_phy = os.path.join('/sys/kernel/debug/ieee80211', phy_iface)
    try:
        dir_athk = glob.glob(os.path.join(path_to_phy, 'ath*'))[0]
    except IndexError:
        return dict()  # error, didn't find ath9k or ath10k
    path_to_xmit = os.path.join(path_to_phy, dir_athk, 'xmit')
    ret = decode_xmit(path_to_xmit)
    LOG.debug("xmit: {}", ret)
    return ret


def get_ifconfig(interface, path_ifconfig=__PATH_IFCONFIG):
    """ get data from ifconfig <interface>.

        @param interface: the wireless interface name, e.g. wlan0
        @param path_ifconfig: path to ifconfig

        @return: the ifconfig fields
        @rtype: dict
    """
    cmd = "{} {}".format(os.path.join(path_ifconfig, 'ifconfig'), interface)
    LOG.debug(cmd)
    with os.popen(cmd) as p:
        ret = decode_ifconfig(p.readlines())
    LOG.debug("ifconfig: {}", ret)
    return ret


def get_iw_stations(interface, path_iw=__DEFAULT_IW_PATH):
    """ executes "iw station dump"

        @param interface: the wireless interface name, e.g. wlan0
        @param path_iw: path to iw

        @return: the command fields
        @rtype: dict
    """
    cmd = "{} dev {} station dump".format(os.path.join(path_iw, 'iw'), interface)
    LOG.debug(cmd)
    with os.popen(cmd) as p:
        data = p.read().replace('\t', '').split('\n')
    result = decode_iw_station(data)
    LOG.debug("iw stations: {}", result)
    return result


def get_status(path_hostapd_cli=__DEFAULT_HOSTAPD_CLI_PATH):
    """ get information from "hostapd_cli status"
        TODO: what if the interface has multiple SSIDs ???

        @param path_hostapd_cli: path to hostapd_cli

        @return: the returned command fields
        @rtype: dict
    """
    cmd = "{} status".format(os.path.join(path_hostapd_cli, 'hostapd_cli'))
    LOG.debug(cmd)
    with os.popen(cmd) as p:
        data = p.read()
    ret = decode_hostapd_status(data)
    LOG.debug("hostapd status: {}", ret)
    return ret


def change_channel(interface, new_channel, count=1, ht_type=None, path_hostapd_cli=__DEFAULT_HOSTAPD_CLI_PATH):
    """ set the AP's channel using "hostapd_cli chan_switch" command.
        TODO: add other optional parameters
              [sec_channel_offset=] [center_freq1=] [center_freq2=] [bandwidth=] [blocktx]

        @param interface: the wireless interface name, e.g. wlan0
        @param new_channel: the new channel number. Trying to change to the current channel returns an error.
        @param ht_type: Valid values are ['', 'ht', 'vht']. Defines the type of channel. Invalid type return an error, e.g. 'vht' in a 802.11g device.
        @param path_hostapd_cli: path to hostapd_cli

        @return: the ifconfig fields
        @rtype: dict
    """
    assert new_channel > 0 and new_channel <= len(valid_frequencies), "{} not in valid channels".format(new_channel)
    frequency = valid_frequencies[new_channel - 1]
    params = "-i {} chan_switch {} {}".format(interface, count, frequency)
    if ht_type in ['ht', 'vht']:
        params += ' ' + ht_type
    cmd = "{} {}".format(os.path.join(path_hostapd_cli, __HOSTAPD_CLI), params)
    LOG.debug(cmd)
    with os.popen(cmd) as p:
        # notice that if you to change to the current channel, the program returns FAIL
        ret = p.read().find('OK') >= 0
    LOG.debug("change chann: {}", ret)
    return ret


def get_stations(path_hostapd_cli=__DEFAULT_HOSTAPD_CLI_PATH):
    """ returns information about all connected stations

        @param path_hostapd_cli: path to hostapd_cli
        @return: dictionary of dictionary
    """
    cmd = "{} all_sta".format(os.path.join(path_hostapd_cli, __HOSTAPD_CLI))
    LOG.debug(cmd)
    with os.popen(cmd) as p:
        data = p.read()
    result = decode_hostapd_station(data)
    LOG.debug("hostapd stations: {}", result)
    return result


def get_iw_info(interface, path_iw=__DEFAULT_IW_PATH):
    """ executes "iw dev info"

        @param interface: the wireless interface name, e.g. wlan0
        @param path_iw: path to iw

        @return: the command fields
        @rtype: dict
    """
    cmd = "{} dev {} info".format(os.path.join(path_iw, 'iw'), interface)
    LOG.debug(cmd)
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
    LOG.debug("iw info: {}", result)
    return result


def get_iwconfig_info(interface, path_iwconfig=__DEFAULT_IWCONFIG_PATH):
    """ get the return from "iwconfig <interface>"
        NOTE: this method only supports (tested) two modes = Managed and Master

        @param interface: interface to change
        @param path_iwconfig: path to iwconfig

        @return: the command fields
        @rtype: dict
    """
    cmd = "{} {}".format(os.path.join(path_iwconfig, 'iwconfig'), interface)
    LOG.debug(cmd)
    with os.popen(cmd) as p:
        result = {'interface': interface}
        data = p.read()
        r = decode_iwconfig(data)
        result.update(r)
    LOG.debug("iwconfig: {}", result)
    return result


def get_power(interface, path_iw=__DEFAULT_IW_PATH, path_iwconfig=__DEFAULT_IWCONFIG_PATH):
    """ get the power in the interface (from a station or AP)

        @param interface: interface to change
        @param path_iw: path to iw

        @return: the command fields
        @rtype: dict
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
    LOG.debug("txpower: {}", txpower)
    return txpower


def set_iw_power(interface, new_power, path_iw=__DEFAULT_IW_PATH):
    """ command dev <devname> set txpower <auto|fixed|limit> [<tx power in mBm>]
        NOTE: this module needs to run as superuser to set the power

        @param interface: interface to change
        @param new_power: can be a string 'auto', or a number (int or float) that represents the new power in dBm
        @param path_iw: path to iw

        @return: if the command succeded
    """
    iw_cmd = "{}".format(os.path.join(path_iw, 'iw'))
    if new_power == 'auto':
        cmd = "{} dev {} set txpower auto".format(iw_cmd, interface)
    elif isinstance(new_power, int) or isinstance(new_power, float):
        new_power = int(float(new_power) * 100)
        cmd = "{} dev {} set txpower fixed {}".format(iw_cmd, interface, new_power)
    else:
        return -1  # error
    LOG.debug(cmd)
    with os.popen(cmd) as p:
        ret = p.read()
    return ret


def disassociate_sta(mac_sta, path_hostapd_cli=__DEFAULT_HOSTAPD_CLI_PATH):
    """ sends the command to disassociate a station

        @param mac_sta: the MAC address of the station we want to disassociate

        @return: if the command succeded
        @rtype: bool
    """
    cmd = "{} disassociate {}".format(os.path.join(path_hostapd_cli, __HOSTAPD_CLI), mac_sta)
    LOG.debug(cmd)
    with os.popen(cmd) as p:
        ret = p.read()
    return 'OK' in ret


def get_config(path_hostapd_cli=__DEFAULT_HOSTAPD_CLI_PATH):
    """ executes "hostapd_cli get_config"

        @param path_hostapd_cli: path to hostapd_cli

        @return: dictionary {'ssid': 'ethanolQL1',
                            'bssid': 'b0:aa:ab:ab:ac:11',
                            'rsn_pairwise_cipher': 'CCMP',
                            'group_cipher': 'CCMP',
                            'key_mgmt': 'WPA-PSK',
                            'wpa': '2',
                            'wps_state': 'disabled'}
    """
    cmd = "{} get_config".format(os.path.join(path_hostapd_cli, __HOSTAPD_CLI))
    LOG.debug(cmd)
    with os.popen(cmd) as p:
        result = p.read().split('\n')
    result.pop(0)  # remove first line (blank line)
    result = dict([w for w in [v.split('=') for v in result] if len(w) == 2])
    return result


def get_iw_survey(interface, path_iw=__DEFAULT_IW_PATH):
    """ executes command "iw dev <interface> survey dump"

        @param interface: interface to change
        @param path_iw: path to iw

        @return: decoded information from survey
    """
    cmd = "{} dev {} survey dump".format(os.path.join(path_iw, 'iw'), interface)
    LOG.debug(cmd)
    with os.popen(cmd) as p:
        data = p.read()
    result = decode_survey(data)
    return result


def get_iw_scan_full(interface, path_iw=__DEFAULT_IW_PATH):
    """ execute command "iw dev <interface> scan dump"

        @param interface: interface to change
        @param path_iw: path to iw

        @return: decoded information from scan dump
    """
    if get_iwconfig_info(args.iface)['Mode'].lower() == 'master':
        cmd = "sudo {} dev {} scan ap-force".format(os.path.join(path_iw, 'iw'), interface)
    else:
        cmd = "sudo {} dev {} scan dump".format(os.path.join(path_iw, 'iw'), interface)
    LOG.debug(cmd)
    with os.popen(cmd) as p:
        data = p.read()
    result = decode_scan(data)
    return result


def get_iw_scan_mac(interface, path_iw=__DEFAULT_IW_PATH):
    """ executes the command "iw dev <interface> scan dump"

        @param interface: interface to scan
        @param path_iw: path to iw

        @return: decoded information from scan dump, only the detected MACs
    """
    cmd = "sudo {} dev {} scan dump 2>&1".format(os.path.join(path_iw, 'iw'), interface)
    LOG.debug(cmd)
    with os.popen(cmd) as p:
        data = p.read()
    result = decode_scan_mac(data)
    return result


def get_iw_scan(interface, path_iw=__DEFAULT_IW_PATH):
    """ command  dev <interface> scan dump

        @param interface: interface to scan
        @param path_iw: path to iw

        @return: decoded information from scan dump, only the detected MACs
    """
    cmd = "sudo {} dev {} scan dump 2>&1".format(os.path.join(path_iw, 'iw'), interface)
    LOG.debug(cmd)
    with os.popen(cmd) as p:
        data = p.read()
    result = decode_scan_basic(data)
    return result


def trigger_scan(interface, path_iw=__DEFAULT_IW_PATH):
    """ command  dev <interface> scan trigger
        it is necessary to call this method before call any method with 'scan',
        it forces the AP to scan all valid channels, and populate the statistics

        @param interface: interface to scan
        @param path_iw: path to iw

        @return: nothing
    """
    cmd = "sudo {} dev {} scan trigger".format(os.path.join(path_iw, 'iw'), interface)
    LOG.debug(cmd)
    os.system(cmd)


def get_phy_with_wlan(interface, path_iw=__DEFAULT_IW_PATH):
    """
        @param interface: the name of the interface, e.g. 'wlan0'
        @return: a string with the phy interface name
    """
    phy_ = get_iw_info(interface, path_iw=path_iw).get('wiphy', '')
    if phy_ == '':
        return None
    else:
        return 'phy{}'.format(phy_)


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
            set_iw_power(args.iface, new_power=new_power, path_iw=args.path_iw)
        if args.verbose:
            print('Power: {}'.format(get_power(interface=args.iface, path_iw=args.path_iw)))

    if args.disassociate is not None:
        disassociate_sta(args.disassociate)

    # print(get_config(path_hostapd_cli=args.path_hostapd_cli))

    if args.survey:
        ret = get_iw_survey(args.iface)
        for k in ret:
            print("Channel: {}".format(k))
            for w in ret[k]:
                print('\t{}: {}'.format(w, ret[k][w]))

    if args.iwconfig:
        ret = get_iwconfig_info(args.iface)
        print("iwconfig", ret)
