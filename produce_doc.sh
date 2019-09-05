#!/bin/bash
#
# generates the help (documentation) of this module
# outputs a pdf file in the doc folder
#
# needs: epydoc
#
# install epydoc:
# ===============
#
# to generate the PDF file, some latex packages are needed:
#
# sudo apt-get install texlive-base
# sudo apt-get install texlive-extra-utils
# sudo apt-get install texlive-latex-recommended
#
#
# opçao 1)
# apt-get install python-epydoc
#
# opcao 2)
#
# wget -q http://prdownloads.sourceforge.net/epydoc/epydoc-3.0.1.tar.gz
# gunzip epydoc-3.0.1.tar.gz
# tar -xvf epydoc-3.0.1.tar
# cd epydoc-3.0.1/
# make install
# make installdocs

EPIDOC=`which epydoc`
if [ "$EPIDOC" == "" ]; then
    sudo apt-get install python-epydoc
fi

PDF_FILE="command-ap-api"
epydoc --pdf --name api -o temp --graph all * 1>/dev/null 2>&1
mv "temp/api.pdf" "$PDF_FILE.pdf"
rm -fr temp

#if [ ! -d doc ]; then
#    mkdir doc
#fi
#epydoc --html --name api -o doc --graph all * 1>/dev/null 2>&1


# delete .pyc files
find . -name "*.pyc" -exec rm {} \;
