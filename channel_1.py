import socket
# import Measurements
# from Measurements import TIME_FORMAT
from threading import Thread
from _datetime import datetime
import os
import time
import argparse


# UDP_IP = "10.1.30.36"
UDP_IP = "192.168.43.205"
# UDP_IP = "192.168.1.65"
# UDP_IP = "192.168.1.241"
__version__ = '0.0.1'

TIME_FORMAT = '%Y-%m-%d-%H:%M:%S.%f'

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timestep-detect', type=float, default=0.001, help='Step between measurements, s')
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
    return parser.parse_args()

def get_sleep_time(timestep_detect):
    current_time = time.time()
    time2sleep = timestep_detect - current_time % timestep_detect

    return time2sleep

class ClientThread(Thread):

    def __init__(self, UDP_IP, channel, sensor_type, player):
        super().__init__()
        self.UDP_IP = UDP_IP
        self.channel = channel
        self.sensor_type = sensor_type
        self.player = player

        port_server, port_client = self.get_server_client_ports(channel, sensor_type, player)
        self.UDP_PORT_RECEIVE = port_client
        self.UDP_PORT_SEND = port_server

        self.socket_receiver = socket.socket(socket.AF_INET,  # Internet
                                        socket.SOCK_DGRAM)  # UDP
        self.socket_receiver.bind((self.UDP_IP, self.UDP_PORT_RECEIVE))

    @staticmethod
    def get_server_client_ports(channel, sensor_type, player):
        port_server = '6' + channel + sensor_type + player
        port_client = '60' + channel + sensor_type

        return int(port_server), int(port_client)

    def __repr__(self):
        repr = 'UDP_IP=' + str(self.UDP_IP) + ',' + 'UDP_PORT_RECEIVE=' + str(self.UDP_PORT_RECEIVE) + \
            ',' + 'UDP_PORT_SEND=' + str(self.UDP_PORT_SEND)

        return repr

    def get_response_msg(self):
        return ''

    def respond(self, response_address):
        response_msg = self.get_response_msg()
        self.socket_receiver.sendto(response_msg, response_address)


class StatusThread(ClientThread):

    def __init__(self, UDP_IP, channel, sensor_type, player, key_order=None):
        super().__init__(UDP_IP, channel, sensor_type, player)

        # self.socket_receiver = socket_receiver
        # self.UDP_PORT_SEND = UDP_PORT_SEND
        self.info_dict = {}
        if key_order is None:
            self.key_order = ['sensor_name', 'version', 'support_cmd', 'status']

    # def update_info(self, key, value):
    #     self.info_dict[key] = value

    def __setitem__(self, key, value):
        self.info_dict[key] = value

    def __repr__(self):
        # repr = self.__class__.__name__ + '_' + str(self.info_dict)
        # repr = self.__class__.__name__ + '_' + str(self.get_response())
        repr = self.__class__.__name__ + '__' + super().__repr__() + '__' + str(self.get_response_msg())
        return repr

    def get_response_msg(self):
        response_values = []

        for key in self.key_order:
            value2append = self.info_dict.get(key, '')
            response_values.append(value2append)

        response_msg = ','.join(response_values)

        return response_msg

print('starting StatusThread')
status_thread = StatusThread(
    UDP_IP=UDP_IP,
    channel='1',
    sensor_type='07',
    player='1',
)
print('ending StatusThread')

status_thread['version'] = __version__
status_thread['sensor_name'] = 'smartchair'
status_thread['support_cmd'] = '1'
status_thread['status'] = 'ok'

status_thread.start()

# status_thread.respond()


class TimeThread(ClientThread):

    def __init__(self, UDP_IP, channel, sensor_type, player, key_order=None):
        super().__init__(UDP_IP, channel, sensor_type, player)

    def run(self):
        while True:
            msg, addr = self.socket_receiver.recvfrom(1024)  # buffer size is 1024 bytes
            msg = msg.decode()
            print("received message:", msg)
            print("sender:", addr)
            sender_ip = addr[0]
            response_address = (sender_ip, self.UDP_PORT_SEND)

            response_msg = datetime.now().strftime(TIME_FORMAT)[:-3]
            self.socket_receiver.sendto(response_msg, response_address)

    def get_response_msg(self):
        response_msg = datetime.datetime.now().strftime(TIME_FORMAT)[:-3]

        return response_msg

    def respond(self, response_address):
        response_msg = self.get_response_msg()
        self.socket_receiver.sendto(response_msg, response_address)

    def __repr__(self):
        repr = self.__class__.__name__ + '__' + super().__repr__()
        return repr


print('starting TimeThread')
time_thread = TimeThread(
    UDP_IP=UDP_IP,
    channel='2',
    sensor_type='07',
    player='1',
)
print('ending TimeThread')

thread = Thread()
thread.start()


class MeasurementsThread(ClientThread):

    def __init__(self,
                 UDP_IP,
                 channel,
                 sensor_type,
                 player,
                 mpu9250,
                 timestep_detect,
                 max_time,
                 verbose,
                 label,
                 person_id,
                 meta,
                 send_data,
                 save_data,
                 folder,
                 synchronize_time,
                 ):
        super().__init__(UDP_IP, channel, sensor_type, player)


        self.timestep_detect = timestep_detect
        self.max_time = max_time
        self.verbose = verbose
        self.label = label
        self.person_id = person_id
        self.meta = meta
        self.send_data = send_data
        self.save_data = save_data
        self.folder = folder
        self.synchronize_time = synchronize_time
        self.mpu9250 = mpu9250

        self.stop = False  # Stop variable

        self.batch_size = int(timestep_send / timestep_detect)  # Количество измерений в одном файле
        self.n_batches = int(max_time / timestep_send)  # Количество отправок

    def stop_measurements(self):
        self.stop = True
        print('Stopping')

    def run(self):
        if self.folder is None:
            folder = datetime.now().strftime(TIME_FORMAT)[:-3]
        else:
            folder = self.folder

        prefix = '../data/' + folder + '/'
        # os.mkdir('../data/' + folder)  # Here we will store data in batches
        os.mkdir(prefix)  # Here we will store data in batches
        data_header = ['datetime_now', 'acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z', 'mag_x', 'mag_y',
                       'mag_z']
        data_header2write = ','.join(data_header) + '\n'


        for n_batch in range(self.n_batches):
            filename = prefix + str(n_batch) + '.csv'
            file = open(filename, 'w')
            file.write(data_header2write)
            for n_measurement in range(self.batch_size):
                data_accelerometer = self.mpu9250.readAccel()
                data_gyroscope = self.mpu9250.readGyro()
                # data_magnetometer = self.mpu9250.readMagnet()

                data_magnetometer = {
                    'x': -1,
                    'y': -1,
                    'z': -1,
                }

                if verbose:
                    if (n_measurement % verbose) == 0:
                        print('data_accelerometer: ', data_accelerometer)
                        print('data_gyroscope: ', data_gyroscope)
                        print('data_magnetometer: ', data_magnetometer)

                measurement_data = [
                    datetime.now().isoformat(),
                    data_accelerometer['x'],
                    data_accelerometer['y'],
                    data_accelerometer['z'],
                    data_gyroscope['x'],
                    data_gyroscope['y'],
                    data_gyroscope['z'],
                    data_magnetometer['x'],
                    data_magnetometer['y'],
                    data_magnetometer['z'],
                ]

                measurement_data = [str(value) for value in measurement_data]

                data2write = ','.join(measurement_data) + '\n'
                file.write(data2write)

                if self.stop:
                    break

                if n_measurement != self.batch_size - 1:  # Because if n_measurement != batch_size - 1 we need to consider time for file.close()
                    time2sleep = get_sleep_time(self.timestep_detect)
                    time.sleep(time2sleep)

            file.close()

            if self.stop:
                break

            time2sleep = get_sleep_time(self.timestep_detect)
            time.sleep(time2sleep)


        print('---------------------------')
        print('----End of measurements----')
        print('---------------------------')



if __name__ == '__main__':
    import FaBo9Axis_MPU9250
    mpu9250 = FaBo9Axis_MPU9250.MPU9250()

    args = parse_args()

    timestep_detect = args.timestep_detect  # timestep between measurements
    timestep_send = args.timestep_send  #  timestep between sendings
    max_time = args.max_time  # total time of measurement
    verbose = args.verbose
    label = args.label
    person_id = args.person_id
    meta = args.meta
    send_data = args.send_data
    save_data = args.save_data
    folder = args.folder
    synchronize_time = args.synchronize_time

    # mpu9250 = None  # Temporary solution

    measurements_thread = MeasurementsThread(
        UDP_IP,
        '3',
        '07',
        '1',
        mpu9250,
        timestep_detect,
        max_time,
        verbose,
        label,
        person_id,
        meta,
        send_data,
        save_data,
        folder,
        synchronize_time,
    )

    measurements_thread.start()
    time.sleep(3)
    print('I am doing other stuff')
    time.sleep(3)
    print('Trying to stop')
    measurements_thread.stop_measurements()
    measurements_thread.join()


class CmdThread(ClientThread):

    def __init__(self, UDP_IP, channel, sensor_type, player, key_order=None):
        super().__init__(UDP_IP, channel, sensor_type, player)

    def run(self):
        while True:
            msg, addr = self.socket_receiver.recvfrom(1024)  # buffer size is 1024 bytes
            msg = msg.decode()
            print("received message:", msg)
            print("sender:", addr)
            sender_ip = addr[0]
            response_address = (sender_ip, self.UDP_PORT_SEND)

            msg_parts = msg.split(',')
            msg_num = int(msg_parts[0])

            time_sync_source = 'ntp1.stratum1.ru'
            current_state = 'non_itinialized'

            if msg_num == 1:  # Reset
                pass
            elif msg_num == 2:  # Start
                pass  # run Measurements.py
            elif msg_num == 3:  # Stop
                pass  # stop Measurements.py
            elif msg_num == 4:  # Time sync
                pass  # os.command(time_sync_command)
            elif msg_num == 5:  # Time sync source
                if len(msg_parts) >= 2:
                    new_time_sync_source = msg_parts[1]
                    try:
                        time_sync_source = str(new_time_sync_source)
                    except:
                        print('Fail to set the new time_sync_source')
            elif msg_num == 6:  # Start time sending
                pass
            elif msg_num == 7:  # State
                response_msg = current_state  # send it?
                pass
            elif msg_num == 8:  # Send last measurement data
                pass
            elif msg_num == 9:
                pass  # Set new IP and player number















