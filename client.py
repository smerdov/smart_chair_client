import socket
from threading import Thread
from _datetime import datetime
import os
import time
import argparse
from threads import SenderThread, ListenerThread, get_server_client_ports, get_socket, get_ports_adresses_sockets
from config import channels_dict, TIME_FORMAT, __version__
from threads import StatusThread, TimeThread, AcknowledgementThread, MeasurementsThread, CmdThread
import FaBo9Axis_MPU9250
import pandas as pd

# wd = os.getcwd()  # TODO: think about ip
# if wd.startswith('/home'):  # It's RPI
#     UDP_IP = "192.168.43.205"  # For client at home
# else:  # It's Mac
#     UDP_IP = "192.168.43.154"  # For server at home
#
# # UDP_IP = "10.1.30.36"
# # UDP_IP = "192.168.1.65"
# # UDP_IP = "192.168.1.241"

def get_config():
    config = {}

    with open('server.cfg') as file:
        config['ip_server'] = file.readline()

    with open('player.cfg') as file:
        config['player_id'] = file.readline()

    df_config = pd.read_csv('rt_en.cfg', header=None)
    config['periodic_sending'] = df_config.iloc[0, 0]
    config['periodic_sending_use_ftp'] = df_config.iloc[1, 0]
    config['periodic_sending_period'] = df_config.iloc[2, 0]
    config['periodic_sending_ip'] = df_config.iloc[3, 0]

    return config


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timestep-detect', type=float, default=0.01, help='Step between measurements, s')
    parser.add_argument('--timestep-send', type=float, default=30, help='Step between sending batches, s')  # Actually it has different meaning now
    parser.add_argument('--max-time', type=float, default=12 * 60 * 60, help='Maximum measurement time, s')  # 12 hours
    parser.add_argument('--verbose', type=int, default=0)
    parser.add_argument('--send-data', type=bool, default=False, help='Whether to send data to server')
    parser.add_argument('--save-data', type=bool, default=True, help='Whether to save data locally')
    parser.add_argument('--label', type=str, default='')
    parser.add_argument('--meta', type=str, default='')
    parser.add_argument('--person-id', type=str, default='')
    parser.add_argument('--folder', type=str, default=None)
    parser.add_argument('--synchronize-time', type=bool, default=False)
    parser.add_argument('--wait', type=float, default=0)
    args = parser.parse_args()
    args = vars(args)

    return args


if __name__ == '__main__':
    config = get_config()
    mpu9250 = FaBo9Axis_MPU9250.MPU9250()
    measurement_thread_kwargs = parse_args()
    print('measurement_thread_kwargs = ', measurement_thread_kwargs)

    wait = measurement_thread_kwargs['wait']
    time.sleep(wait)

    ports, addresses, sockets = get_ports_adresses_sockets(channels_dict=channels_dict, sensor_id='07',
                            player_id=config['player_id'], ip_server=config['ip_server'], get_server_sockets=False,
                            get_client_sockets=True)

    status_thread = StatusThread(
        addresses['server']['status'],
        # addresses['client']['status'],
        # ('192.168.1.100', 61070),
        sockets['client']['status'],
    )
    status_thread['version'] = __version__
    status_thread['sensor_name'] = 'smartchair'
    status_thread['support_cmd'] = '12345679'
    status_thread['status'] = 'ok'
    status_thread.start()

    time_thread = TimeThread(
        # '255.255.255.255',
        addresses['server']['time'],
        # ('255.255.255.255', 62070),
        # ('192.168.1.100', 62070),
        # addresses['client']['time'],
        sockets['client']['time'],
    )
    time_thread.start()

    acknowledgement_thread = AcknowledgementThread(
        addresses['server']['ack'],
        # addresses['client']['ack'],
        # ('192.168.1.100', 65070),
        # '255.255.255.255',
        sockets['client']['ack'],
    )
    acknowledgement_thread.start()

    cmd_thread = CmdThread(
        sockets['client']['cmd'],
        addresses,
        status_thread,
        time_thread,
        # measurements_thread,
        acknowledgement_thread,
        mpu9250,
        measurement_thread_kwargs,
        player_id=config['player_id'],
        # *args,
        verbose=False,
        sockets=sockets,
        # **kwargs
    )
    cmd_thread.start()
    print('Client is started')








