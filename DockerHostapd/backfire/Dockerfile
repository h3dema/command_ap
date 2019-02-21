FROM ubuntu:14.04
RUN apt-get -y update
RUN apt-get -y upgrade

RUN apt-get install -qq wget unzip
RUN apt-get install -qq build-essential git git-core
RUN apt-get install -qq cmake gcc libcunit1-dev libudev-dev

RUN apt-get -y install libncurses5-dev zlib1g-dev gawk flex quilt libssl-dev xsltproc libxml-parser-perl mercurial bzr ecj cvs binutils patch bzip2 make gettext pkg-config libz-dev

RUN apt-get -y install subversion
RUN svn checkout svn://svn.openwrt.org/openwrt/tags/backfire_10.03.1/

RUN cd backfire_10.03.1;./scripts/feeds update -a
RUN cd backfire_10.03.1;./scripts/feeds install -a

## este endereço não funciona pois
## só retorna openwrt == 17+
# git clone https://git.openwrt.org/openwrt/openwrt.git
# git checkout openwrt-17.01
