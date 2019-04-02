import socket
from threading import Thread
from _datetime import datetime
import os
import time
import argparse
from threads import SenderThread, ListenerThread, get_server_client_ports, get_socket, get_ports_adresses_sockets
from threads import channels_dict, ip_server, ip_client, TIME_FORMAT
from threads import StatusThread, TimeThread, AcknowledgementThread, MeasurementsThread, CmdThread
import FaBo9Axis_MPU9250

wd = os.getcwd()  # TODO: think about ip
if wd.startswith('/home'):  # It's RPI
    UDP_IP = "192.168.43.205"  # For client at home
else:  # It's Mac
    UDP_IP = "192.168.43.154"  # For server at home

# UDP_IP = "10.1.30.36"
# UDP_IP = "192.168.1.65"
# UDP_IP = "192.168.1.241"

__version__ = '0.0.1'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timestep-detect', type=float, default=0.01, help='Step between measurements, s')
    parser.add_argument('--timestep-send', type=float, default=10, help='Step between sending batches, s')
    parser.add_argument('--max-time', type=float, default=12 * 60 * 60, help='Maximum measurement time, s')
    parser.add_argument('--verbose', type=int, default=0)
    parser.add_argument('--send-data', type=bool, default=True, help='Whether to send data to server')
    parser.add_argument('--save-data', type=bool, default=True, help='Whether to save data locally')
    parser.add_argument('--label', type=str, default='')
    parser.add_argument('--meta', type=str, default='')
    parser.add_argument('--person-id', type=str, default='')
    parser.add_argument('--folder', type=str, default=None)
    parser.add_argument('--synchronize-time', type=bool, default=False)
    args = parser.parse_args()
    args = vars(args)

    return args


ports, addresses, sockets = get_ports_adresses_sockets(ip_server=ip_server, ip_client=ip_client,
    channels_dict=channels_dict, sensor_id='07', player_id='0', get_server_sockets=False, get_client_sockets=True)


print('Initializaing StatusThread')
status_thread = StatusThread(
    addresses['server']['status'],
    sockets['client']['status'],
)
status_thread['version'] = __version__
status_thread['sensor_name'] = 'smartchair'
status_thread['support_cmd'] = '1'
status_thread['status'] = 'ok'
status_thread.start()
print('Initializaing StatusThread done')


print('Initializaing TimeThread')
time_thread = TimeThread(
    addresses['server']['time'],
    sockets['client']['time'],
)
time_thread.start()
print('Initializaing TimeThread done')


print('Initializaing TimeThread')
acknowledgement_thread = AcknowledgementThread(
    addresses['server']['ack'],
    sockets['client']['ack'],
)
acknowledgement_thread.start()
print('Initializaing TimeThread done')





# timestep_detect = args.timestep_detect  # timestep between measurements
# timestep_send = args.timestep_send  #  timestep between sendings
# max_time = args.max_time  # total time of measurement
# verbose = args.verbose
# label = args.label
# person_id = args.person_id
# meta = args.meta
# send_data = args.send_data
# save_data = args.save_data
# folder = args.folder
# synchronize_time = args.synchronize_time

# mpu9250 = None  # Temporary solution
# response_address = None







# TODO: acknowledgement
# TODO: id and port hot update





if __name__ == '__main__':
    mpu9250 = FaBo9Axis_MPU9250.MPU9250()
    measurement_thread_kwargs = parse_args()

    cmd_thread = CmdThread(
        sockets['client']['cmd'],
        addresses,
        status_thread,
        time_thread,
        # measurements_thread,
        acknowledgement_thread,
        mpu9250,
        measurement_thread_kwargs,
        # *args,
        verbose=False,
        # **kwargs
    )
    print('Starting cmd_thread')
    cmd_thread.start()
    print('cmd_thread is started')








