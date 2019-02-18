FROM ubuntu:14.04
RUN apt-get -y update
RUN apt-get -y upgrade


RUN apt-get install -qq wget unzip build-essential git
RUN apt-get install -qq cmake gcc libcunit1-dev libudev-dev

git clone git://w1.fi/srv/git/hostap.git