#!/bin/bash


is_docker_installed=`dpkg-query -l | grep "docker.io" | wc -l`
if [ "$is_docker_installed" -eq "1" ];
    version=`docker version | grep "Client version" | awk '{print $3}'`
    #dpkg-query -l | grep "docker.io" | echo "`awk '{print $2}'`"
    echo "docker.io version $version is installed"
else
    echo "Please install docker.io"
    echo "sudo apt-get install docker.io"
fi

IDS=`docker ps | grep hostapd | awk '{print $1}'`
for id in $IDS; do
    docker stop $id
done

if [ ! -d bin ]; then
    mkdir bin
fi

# identify Ubuntu version
is_14=`lsb_release -r | grep 14 | wc -l`
is_16=`lsb_release -r | grep 16 | wc -l`
is_18=`lsb_release -r | grep 18 | wc -l`

if [ "$is_14" -eq 1 ]; then
    docker build -t hostapd ./14
elif [ "$is_16" -eq 1 ]; then
    docker build -t hostapd ./16
elif [ "$is_18" -eq 1 ]; then
    docker build -t hostapd ./18
else
    echo "no compatible version"
    exit 0
fi



docker_hostapd_running=`docker ps | grep hostapd | wc -l`
if [ "$docker_hostapd_running" -eq "0" ]; then
    docker run -w /WORKDIR -t -d hostapd
fi

docker ps

ID=`docker ps | grep hostapd | awk '{print $1}'`
docker cp $ID:/WORKDIR/hostap/hostapd/hostapd bin
docker cp $ID:/WORKDIR/hostap/hostapd/hostapd_cli bin
docker cp $ID:/WORKDIR/iw/iw bin

docker stop $ID

ls bin
