# Repository

This repository contains the python codes to control the thesis experiment.
The codes are divided into the following directories

## Dirs

* __cmd__: contains the python codes for executing commands in the AP

* __publisher_subscriber__: contains a test to create a publisher and a subscriber to be used with the command. The publisher runs ``command_ap.py``, where each command in the API has a code. The subscriber subscribes to receive the information.

* __getter_setter__: contains a test to create a http server that receives commands from a client. The client can send get or set commands. The server runs ``command_ap.py``.


All other dirs are tests. **Please don't use them**


## Install the AP

To install an AP and other wireless tools in Ubuntu use the following commands

```bash
sudo apt-get install hostapd
sudo apt-get install iw wireless-tools
```

## Running the AP

To run the AP in a linux, you need the previous tools installed, and you need to configure the hostapd.
The configuration file is hostapd.conf (see an example in the directory).

You will need to change the following fields in the file:
* __interface__ is wlan0 in my case, but you need to put here the name of your wireless interface
* __bssid__ is the mac address of your computer's wireless network card
* __channel__ set the channel number from 1 to 11 (in Brazil)
* __ssid__ defines the wifi network name
* __wpa_password__ is a string that defines the wifi network passphrase

# Requisites

* iw: The command uses __iw__ to get and set some parameters in the wifi interface. It was tested using __iw__ version 4.9 and 5.3 on Ubuntu. Notice that this tool comes with different versions depending on the Ubuntu's own version. Thus we recommend download and compile it from the source.

```
git clone git://git.kernel.org/pub/scm/linux/kernel/git/jberg/iw.git
cd iw
make
sudo make install
```

