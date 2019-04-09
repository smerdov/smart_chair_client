#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket

# UDP_IP = "10.1.30.36"
UDP_IP = "192.168.43.154"
UDP_PORT = 65000

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print ("received message:", data.decode())

