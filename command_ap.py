#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import argparse


valid_frequency = [2412 + i * 5 for i in range(13)]
__HOSTAPD_CLI = "hostapd_cli"


def get_hostapd(path_hostapd_cli='.'):
    return os.path.join(path_hostapd_cli, __HOSTAPD_CLI)


def get_status():
    cmd = "{} {}".format(get_hostapd(), "status")
    with os.popen(cmd) as p:
        lines = p.read().split('\n')
    ret = dict([v for v in [a.split("=") for a in lines] if len(v) == 2])
    for k in ret:
        try:
            ret[k] = int(ret[k])
        except ValueError:
            pass
    return ret


def change_channel(new_channel, count=1):
    assert new_channel > 0 and new_channel <= len(valid_frequency), "{} not in valid channels".format(new_channel)
    frequency = valid_frequency[new_channel - 1]
    params = "chan_switch {} {}".format(count, frequency)
    cmd = "{} {}".format(get_hostapd(), params)
    with os.popen(cmd) as p:
        ret = p.read().find('OK') >= 0
    return ret


def get_stations():
    cmd = "{} {}".format(get_hostapd(), "status")
    with os.popen(cmd) as p:
        ret = p.read()
    return ret


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='get wifi info.')
    parser.add_argument('--info', action='store_true', help='show hostapd info')
    parser.add_argument('--increment-channel', action='store_true', help='increment the channel (cycle)')
    parser.add_argument('--stations', action='store_false', help='show stations')
    args = parser.parse_args()

    status = get_status()
    if args.info:
        for k, v in status.items():
            print("{} : {}".format(k, v))

    if args.increment_channel:
        channel = status.get('channel', 1)
        print("curr channel: {}".format(channel))

        channel = (channel + 1) % 11
        if channel == 0:
            channel = 1

        if change_channel(channel):
            print("new channel: {}".format(channel))
        else:
            print("error during channel change")

    if args.stations:
        print(get_stations())
