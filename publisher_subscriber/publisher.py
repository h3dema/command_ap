# -*- coding: utf-8 -*-
#
# works on Python 3
# info: https://pyzmq.readthedocs.io/en/latest/
#
# install:
# pip3 install pyzmq


import zmq
import random
import sys
import time

port = "5556"
if len(sys.argv) > 1:
    port = sys.argv[1]
    int(port)

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)


while True:
    topic = random.randrange(9999, 10005)
    messagedata = random.randrange(1, 215) - 80
    print("topic: %6d msg: %d" % (topic, messagedata))
    socket.send(b"%d %d" % (topic, messagedata))
    time.sleep(1)
