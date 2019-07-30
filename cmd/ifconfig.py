#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re


def decode_ifconfig(data):
    ret = dict()
    lines = data.replace('\t', '').split('\n')
    for line in lines:
        if 'RX packets:' in line:
            packets, errors, dropped, overruns, frame = re.findall(r'\d+', line)
            ret.update({'rx_packets': packets,
                        'rx_errors': errors,
                        'rx_dropped': dropped,
                        'rx_overruns': overruns,
                        'frame': frame,
                        }
                       )
        elif 'TX packets:' in line:
            packets, errors, dropped, overruns, carrier = re.findall(r'\d+', line)
            ret.update({'tx_packets': packets,
                        'tx_errors': errors,
                        'tx_dropped': dropped,
                        'tx_overruns': overruns,
                        'carrier': carrier,
                        }
                       )
        elif line.find('collisions:') >= 0:
            collisions, txqueuelen = re.findall(r'\d+', line)
            ret.update({'collisions': collisions,
                        'txqueuelen': txqueuelen,
                        }
                       )
        elif line.find('RX bytes:') >= 0:
            rx_bytes, rx_scale_bytes, tx_bytes, tx_scale_bytes = re.findall(r'[+-]?\d*\.\d+|\d+', line)
            ret.update({'rx_bytes': rx_bytes,
                        'rx_scale_bytes': rx_scale_bytes,
                        'tx_bytes': tx_bytes,
                        'tx_scale_bytes': tx_scale_bytes,
                        }
                       )
    return ret


if __name__ == '__main__':
    data = """
wlan0     Link encap:Ethernet  HWaddr b0:aa:ab:ab:ac:10  
          inet addr:192.168.10.1  Bcast:192.168.10.255  Mask:255.255.255.0
          inet6 addr: fe80::b2aa:abff:feab:ac10/64 Scope:Link
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:843246 errors:0 dropped:0 overruns:0 frame:0
          TX packets:1650711 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000 
          RX bytes:58009076 (58.0 MB)  TX bytes:2505374616 (2.5 GB)
"""