import socket
# import Measurements
# from Measurements import TIME_FORMAT
from threading import Thread
from _datetime import datetime
import os
import time
import argparse
from threads import SenderThread, ListenerThread, get_server_client_ports, get_socket, get_ports_adresses_sockets
from config import channels_dict, ip_server, ip_client, TIME_FORMAT, __version__


if __name__ == '__main__':
    ports, addresses, sockets = get_ports_adresses_sockets(#ip_server=ip_server, ip_client=ip_client,
        channels_dict=channels_dict, sensor_id='07', player_id='0', get_server_sockets=True, get_client_sockets=False)

    threads = {}
    listening_channels = ['status', 'time', 'data', 'ack']

    for channel_name in listening_channels:
        threads[channel_name] = ListenerThread(sockets['server'][channel_name], name=channel_name, verbose=True)
        threads[channel_name].start()

    threads['cmd'] = SenderThread(addresses['client']['cmd'], sockets['server']['cmd'], name='cmd')

    while True:
        msg = input('Enter a command: ')
        threads['cmd'].send(msg)




















