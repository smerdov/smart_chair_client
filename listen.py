#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
import time
if len(sys.argv) == 2:
    UDP_IP = sys.argv[1]
else:
    UDP_IP = "" #"192.168.0.17" #"192.168.1.201"

UDP_PORT = 60411
print(UDP_IP, UDP_PORT)

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = sock.recvfrom(1024)
    print(data, time.time())

# buffer size is 1024 bytes
