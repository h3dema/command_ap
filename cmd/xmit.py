#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Module xmit
# This module decodes the "xmit" file.
# Returns a dictionary with all decoded fields.
#
#
from __future__ import print_function
from os.path import exists, basename


# contains the title of the lines with data (4 columns each)
lines_with_queue_data = ['MPDUs Queued', 'MPDUs Completed', 'MPDUs XRetried',
                         'Aggregates',
                         'AMPDUs Queued HW', 'AMPDUs Queued SW',
                         'AMPDUs Completed', 'AMPDUs Retried', 'AMPDUs XRetried',
                         'TXERR Filtered', 'FIFO Underrun', 'TXOP Exceeded', 'TXTIMER Expiry',
                         'DESC CFG Error', 'DATA Underrun', 'DELIM Underrun',
                         'TX-Pkts-All', 'TX-Bytes-All',
                         'HW-put-tx-buf', 'HW-tx-start', 'HW-tx-proc-desc',
                         'TX-Failed',
                         ]


def check(line, items):
    for item in items:
        if item in line:
            return True
    return False


def decode_xmit(filename):
    if exists(filename):
        result = dict()
        with open(filename, 'r') as f:
            for line in f:
                if check(line, lines_with_queue_data):
                    i = line.find(":")
                    item = line[:i]
                    r = line[i + 1:].strip().split()
                    result.update({"{}_{}".format(item, "BE"): r[0],
                                   "{}_{}".format(item, "BK"): r[1],
                                   "{}_{}".format(item, "VI"): r[2],
                                   "{}_{}".format(item, "VO"): r[3],
                                   }
                                  )
                elif check(line, ['qlen_be', 'qlen_bk', 'qlen_vi', 'qlen_vo']):
                    r = line.split()
                    result.update({r[0]: r[1],
                                   }
                                  )
                elif line.find('ampdu-depth:') >= 0:
                    r = line.split()
                    item = r.pop(0)[1:-2]
                    for i in range(len(r) // 2):
                        result["{}_{}".format(item, r[i * 2][:-1])] = int(r[i * 2 + 1])
    else:
        result = None
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Decodes the files from ifconfig command output.')
    parser.add_argument('--filename', type=str, default='/sys/kernel/debug/ieee80211/phy0/ath9k/xmit', help='filename')
    args = parser.parse_args()
    result = decode_xmit(args['filename'])
    print("Decoding", args['filename'], ">>", result)
