#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    convert the output of iwconfig into a dictionary

"""


def grab_first(x, k, type=None):
    """
        helper function to decode iwconfig. grabs the first element of the split given by key k

        @param x: string to be splitted by 'espaces'
        @param k: position of the splitted result to be returned
        @param type: valid values are [int, float, None]. If None, return the str, else try to convert to the specified type

        @return: the element 'k'
        @rtype: type
    """
    v = x.split(k)[1].split()[0]
    if type is not None:
        try:
            v = type(v)
        except ValueError:
            pass  # just keep the same value
    return v


"""lambda functions to be applied according to the field"""
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


def decode_iwconfig(data):
    """
        get the output of iwconfig and convert it into a dictionary

        @param data: output of iwconfig captured by the system
        @return: a dictionary with iwconfig fields
    """
    result = dict()
    for line in data.replace('\t', '').split('\n'):
        for k in cmds_iwconfig:
            if k in line:
                f = cmds_iwconfig[k]
                x = f(line)
                result[k] = x
    return result
