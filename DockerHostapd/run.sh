#!/bin/bash

if [ ! -d bin ];
    mkdir bin
fi

docker build -t hostapd .
docker run -w /WORKDIR -v bin:/WORKDIR/bin -it hostapd
