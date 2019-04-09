#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
import time

# print sys.argv
if len(sys.argv) == 2:
	UDP_IP = sys.argv[1]
else:
	UDP_IP = "192.168.1.182"
UDP_PORT = 60411

print("UDP target IP:", UDP_IP)
print("UDP target port:", UDP_PORT)

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM)#,
                     # socket.IPPROTO_UDP) # UDP
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

for i in range(100):
    sock.sendto("4", (UDP_IP, UDP_PORT))
    print(i, time.time())
    time.sleep(0.1)


# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
#
# import socket
#
# # UDP_IP = "10.1.30.40"
# # UDP_IP = "192.168.43.154"
# UDP_IP = "192.168.1.236"
# UDP_PORT = 60107
#
# print("UDP target IP:", UDP_IP)
# print("UDP target port:", UDP_PORT)
#
# sock = socket.socket(socket.AF_INET, # Internet
#                      socket.SOCK_DGRAM) # UDP
# while True:
# 	msg = input("Command: ")
# 	print("message:", msg)
# 	sock.sendto(msg.encode(), (UDP_IP, UDP_PORT))

