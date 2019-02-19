#!/bin/sh

ids=`docker images | grep hostapd | awk '{print $3}'`
for id in $ids; do
    docker rmi -f $id
done