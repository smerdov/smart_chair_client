import socket
# import Measurements
# from Measurements import TIME_FORMAT
from threading import Thread
from _datetime import datetime
import os
import time
import argparse


def get_server_client_ports(channel, sensor_type, player):
    port_server = '6' + channel + sensor_type + player
    port_client = '60' + channel + sensor_type

    return int(port_server), int(port_client)


ip_server = '192.168.43.154'
ip_client = '192.168.43.205'

port_server, port_client = get_server_client_ports(channel='4', sensor_type='07', player='0')
# UDP_PORT_RECEIVE = port_client
# UDP_PORT_SEND = port_server
####### REVERSED
UDP_PORT_RECEIVE = port_server
UDP_PORT_SEND = port_client

socket_receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket_receiver.bind((ip_server, port_server))

msg = '3'
socket_receiver.sendto(msg.encode(), (ip_client, port_client))



