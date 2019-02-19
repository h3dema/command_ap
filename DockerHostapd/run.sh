#!/bin/bash

if [ ! -d bin ]; then
    mkdir bin
fi

# identify Ubuntu version
is_14=`lsb_release -r | grep 14 | wc -l`
is_16=`lsb_release -r | grep 16 | wc -l`
if [ "$is_14" -eq 1 ]; then
    docker build -t hostapd ./14
elif [ "$is_16" -eq 1 ]; then
    docker build -t hostapd ./16
fi

docker run -w /WORKDIR -v "`pwd`/bin":/vol -it hostapd
#"cp /WORKDIR/bin/* /tmp"

