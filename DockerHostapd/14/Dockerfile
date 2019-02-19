FROM ubuntu:14.04
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
RUN apt-get install -y libnl-dev libnl1
RUN apt-get install -y libssl-dev
RUN apt-get install -y libiw-dev
RUN apt-get install -y curl libcurl3 libcurl3-dev
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

#RUN if [ ! -d /WORKDIR/bin ]; then mkdir /WORKDIR/bin; fi& \
#    list_files="hostap/hostapd/hostapd hostap/hostapd/hostapd_cli iw/iw"; \
#    for f in $list_files; do cp "/WORKDIR/$f" /WORKDIR/bin; done
