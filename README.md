# Repository

This repository contains the python codes to control the thesis experiment.
The codes are divided into the following directories

## Dirs

* __cmd__: contains the python codes for executing commands in the AP

* __publisher_subscriber__: contains a test to create a publisher and a subscriber to be used with the command. The publisher runs ``command_ap.py``, where each command in the API has a code. The subscriber subscribes to receive the information.

* __getter_setter__: contains a test to create a socket server that receives commands from a client. The client can send get or set commands. The server runs ``command_ap.py``.


All other dirs are tests. **Please don't use them**