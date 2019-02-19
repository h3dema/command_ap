# Introduction

In this directory we have the tools for generating the __hostapd__, __hostapd_cli__ and __iw__ files required for the operation of the wireless network control.

To create them just run the __run.sh__ command.
It will identify your Ubuntu version (14, 16, or 18) and will generate a docker container to compile the source files. After running, all three programs will be copied to the _bin_ directory in the current directory.

## Requirements

You need to have docker installed. In Ubuntu, to install it use

```bash
sudo apt-get -y install docker.io
sudo usermod -aG docker $USER
newgrp docker
```