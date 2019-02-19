FROM ubuntu:18.04
RUN apt-get -y update
RUN apt-get -y upgrade


RUN apt-get install -qq wget unzip build-essential git
RUN apt-get install -qq cmake gcc libcunit1-dev libudev-dev


# Set environment variables.
ENV HOME /root

# Define working directory.
RUN mkdir /WORKDIR
WORKDIR /WORKDIR

# dependencies
RUN apt-get install -y pkg-config
RUN apt-get install -y libnl-3-dev
RUN apt-get install -y libnl-genl-3-dev
RUN apt-get install -y libssl-dev
RUN apt-get install -y libiw-dev
RUN apt-get install -y curl libcurl4 libcurl4-openssl-dev
RUN apt-get install -y wireless-tools


# clone
RUN cd /WORKDIR & \
    git clone git://git.kernel.org/pub/scm/linux/kernel/git/jberg/iw.git

RUN cd /WORKDIR & \
    git clone git://w1.fi/srv/git/hostap.git

# Compile iw
RUN cd /WORKDIR/iw;make -j4

# config hostapd
COPY config /WORKDIR/hostap/hostapd/.config

# compile hostapd
RUN cd /WORKDIR/hostap/hostapd;make -j4

