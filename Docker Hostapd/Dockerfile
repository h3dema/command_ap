FROM ubuntu:14.04
RUN apt-get -y update
RUN apt-get -y upgrade


RUN apt-get install -qq wget unzip build-essential git
RUN apt-get install -qq cmake gcc libcunit1-dev libudev-dev

RUN apt-get install -y libnl-dev libnl1
RUN apt-get install -y libssl-dev
RUN apt-get install -y libiw-dev
RUN apt-get install -y curl libcurl3 libcurl3-dev
RUN apt-get install -y wireless-tools


RUN mkdir -p /workdir
WORKDIR /workdir
cd /workdir
git clone git://w1.fi/srv/git/hostap.git

cd /workdir/hostapd/hostapd

#make clean
#make ethanol