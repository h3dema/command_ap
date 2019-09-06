#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    convert the output of iw dev station dump into a dictionary

"""
import re


def decode_survey(data):
    """ decodes the data provided by "iw survey dump"

    @param data: output from iw dev survey dump
    @return: dictionary of dictionary
            {2432: {'noise': '-95 dBm',
                    'in use': True,
                    'channel transmit time': '713 ms',
                    'channel busy time': '9479 ms',
                    'channel active time': '54259 ms',
                    'channel receive time': '8279 ms'},
             2467: {},
             }
    """
    lines = data.split('\n')
    result = dict()
    freq = None
    for _l in lines:
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
                k = _l[0]
                v = _l[1]
                f = re.findall(r"[-+]?\d*\.\d+|\d+", v)
                if len(f) > 0:
                    v = f[0]
                    v = float(v)
                result[freq][k] = v
            except IndexError:
                pass
    return result
