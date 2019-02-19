# command_ap

Send commands to configure 802.11 Hostapd
To see more information, use

```bash
$ python3 command_ap.py --help

usage: command_ap.py [-h] [--verbose] [--path-hostapd-cli PATH_HOSTAPD_CLI]
                     [--path-iw PATH_IW] [--iface IFACE] [--info] [--iw]
                     [--increment-channel] [--stations] [--survey]
                     [--power POWER] [--disassociate DISASSOCIATE]

get wifi info.

optional arguments:
  -h, --help            show this help message and exit
  --verbose             verbose
  --path-hostapd-cli PATH_HOSTAPD_CLI
                        path to hostapd_cli
  --path-iw PATH_IW     path to iw
  --iface IFACE         interface to query
  --info                show hostapd info
  --iw                  show hostapd info
  --increment-channel   increment the channel (cycle)
  --stations            show stations
  --survey              survey channels
  --power POWER         set new power in dBm
  --disassociate DISASSOCIATE
                        disassociate station

```


