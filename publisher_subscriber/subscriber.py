# -*- coding: utf-8 -*-
#
# works on Python 3
# info: https://pyzmq.readthedocs.io/en/latest/
#
# install:
# pip3 install pyzmq

import sys
import zmq

port = "5556"
if len(sys.argv) > 1:
    port = sys.argv[1]
    int(port)

if len(sys.argv) > 2:
    port1 = sys.argv[2]
    int(port1)

# Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)

print("Collecting updates from weather server...")
socket.connect("tcp://localhost:%s" % port)

if len(sys.argv) > 2:
    socket.connect("tcp://localhost:%s" % port1)

# Subscribe to zipcode, default is NYC, 10001
topicfilter = "10001"
print("For topic", topicfilter)
socket.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

# Process 5 updates
total_value = 0
for update_nbr in range(5):
    string = socket.recv()
    topic, messagedata = [int(v) for v in string.split()]
    total_value += int(messagedata)
    print('topic', topic, 'msg', messagedata)

print("Average messagedata value for topic '%s' was %dF" % (topicfilter, total_value / update_nbr))

