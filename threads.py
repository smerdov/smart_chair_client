import socket
from threading import Thread
from collections import defaultdict
from datetime import datetime
import os
import time
from config import channels_dict, ip_server, ip_client, TIME_FORMAT, __version__


def get_server_client_ports(channel_id, sensor_id, player_id):
    port_server = '6' + channel_id + sensor_id + player_id
    port_client = '60' + channel_id + sensor_id

    return int(port_server), int(port_client)

def get_socket(ip, port):
    socket_receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_receiver.bind((ip, port))

    return socket_receiver

def get_ports_adresses_sockets(ip_server, ip_client, channels_dict, sensor_id, player_id,
                               get_server_sockets=True, get_client_sockets=False):
    ports = defaultdict(dict)
    addresses = defaultdict(dict)
    sockets = defaultdict(dict)

    for channel_name, channel_id in channels_dict.items():
        ports['server'][channel_name], ports['client'][channel_name] = get_server_client_ports(
            channel_id=channel_id,
            sensor_id=sensor_id,
            player_id=player_id)
        addresses['server'][channel_name] = (ip_server, ports['server'][channel_name])
        addresses['client'][channel_name] = (ip_client, ports['client'][channel_name])

        if get_server_sockets:
            sockets['server'][channel_name] = get_socket(ip_server, ports['server'][channel_name])

        if get_client_sockets:
            sockets['client'][channel_name] = get_socket(ip_client, ports['client'][channel_name])

    return ports, addresses, sockets


class SocketThread(Thread):

    def __init__(self, socket, name=None):
        super().__init__()

        self.socket = socket
        if name is not None:
            self.name = name

    def send(self, msg, address):
        """
        :param address: tuple (ip, port)
        :param msg: string message
        """
        self.socket.sendto(msg.encode(), address)


class ListenerThread(SocketThread):

    def __init__(self, *args, verbose=False, **kwargs):
        super().__init__(*args, **kwargs)

        self.verbose = verbose

    def run(self):
        print('Thread ' + self.name + ' are listening...')
        while True:
            msg, addr = self.socket.recvfrom(1024)  # buffer size is 1024 bytes
            msg = msg.decode()
            if self.verbose:
                print("received message:", msg)
                print("sender:", addr)


class SenderThread(SocketThread):

    def __init__(self, opponent_address, *args, period=0.1, **kwargs):
        super().__init__(*args, **kwargs)
        self.opponent_address = opponent_address
        self.period = period
        self.periodic_sending = False

    def __repr__(self):
        repr = self.__class__.__name__ + '__' + super().__repr__()
        return repr

    def get_response_msg(self):
        return 'not implemented yet'

    def send(self, msg=None, address=None):
        if msg is None:
            msg = self.get_response_msg()

        if address is None:
            address = self.opponent_address

        self.socket.sendto(msg.encode(), address)

    def run(self):
        while True:
            if self.periodic_sending:
                self.send()

            time.sleep(self.period)


class StatusThread(SenderThread):

    def __init__(self, *args, key_order=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.info_dict = {}
        if key_order is None:
            self.key_order = ['sensor_name', 'version', 'support_cmd', 'status']

    def __setitem__(self, key, value):
        self.info_dict[key] = value

    def __repr__(self):
        repr = self.__class__.__name__ + '__' + super().__repr__() + '__' + str(self.get_response_msg())
        return repr

    def get_response_msg(self):
        response_values = []

        for key in self.key_order:
            value2append = self.info_dict.get(key, '')
            response_values.append(value2append)

        response_msg = ','.join(response_values)

        return response_msg


class TimeThread(SenderThread):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_response_msg(self):
        response_msg = datetime.now().strftime(TIME_FORMAT)[:-3]

        return response_msg

    def send(self, msg=None, address=None):
        if msg is None:
            msg = self.get_response_msg()

        if address is None:
            address = self.opponent_address

        self.socket.sendto(msg.encode(), address)


class AcknowledgementThread(SenderThread):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ### That's actually the same in this form


class MeasurementsThread(SocketThread):

    def __init__(self,
                 socket,
                 response_address,
                 mpu9250,
                 # *args,
                 kwargs,
                 package_num=0,
                 ):
        ### WTF??? kwargs doesn't work in the init above
        # super().__init__(socket, *args, **kwargs)
        super().__init__(socket)# , **kwargs)

        self.socket = socket
        self.response_address = response_address
        self.mpu9250 = mpu9250

        self.timestep_detect = kwargs['timestep_detect']
        self.timestep_send = kwargs['timestep_send']
        self.max_time = kwargs['max_time']
        self.verbose = kwargs['verbose']
        self.label = kwargs['label']
        self.person_id = kwargs['person_id']
        self.meta = kwargs['meta']
        self.send_data = kwargs['send_data']
        self.save_data = kwargs['save_data']
        self.folder = kwargs['folder']
        self.synchronize_time = kwargs['synchronize_time']

        self.stop = False  # Stop variable

        self.batch_size = int(self.timestep_send / self.timestep_detect)  # Количество измерений в одном файле
        self.n_batches = int(self.max_time / self.timestep_send)  # Количество отправок
        self.package_num = package_num

    def stop_measurements(self):
        self.stop = True
        print('Stopping')

    @staticmethod
    def get_sleep_time(timestep_detect):
        current_time = time.time()
        time2sleep = timestep_detect - current_time % timestep_detect

        return time2sleep

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

                if self.verbose:
                    if (n_measurement % self.verbose) == 0:
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

                measurement_data4server = [
                    str(self.package_num),  # n
                    measurement_data[0][:-3],  # microseconds are ignored
                ] + measurement_data[1:]

                # data2send = str(self.package_num) + ',' + ','.join(measurement_data)  # New line character is not added
                data2send = ','.join(measurement_data4server)  # New line character is not added
                if self.send_data:
                    self.socket.sendto(data2send.encode(), self.response_address)  # TODO: add number of row n

                self.package_num += 1

                if self.stop:
                    break

                if n_measurement != self.batch_size - 1:  # Because if n_measurement != batch_size - 1 we need to consider time for file.close()
                    time2sleep = self.get_sleep_time(self.timestep_detect)
                    time.sleep(time2sleep)

            file.close()

            if self.stop:
                break

            time2sleep = self.get_sleep_time(self.timestep_detect)
            time.sleep(time2sleep)


        print('---------------------------')
        print('----End of measurements----')
        print('---------------------------')


class CmdThread(ListenerThread):

    def __init__(self,
                 socket,
                 addresses,
                 status_thread,
                 time_thread,
                 # measurements_thread,
                 acknowledgement_thread,
                 mpu9250,
                 measurement_thread_kwargs,
                 *args,
                 verbose=False,
                 sockets=None,
                 **kwargs):
        super().__init__(socket, *args, verbose=verbose, **kwargs)
        self.addresses = addresses
        self.status_thread = status_thread
        self.time_thread = time_thread
        # self.measurements_thread = measurements_thread
        self.acknowledgement_thread = acknowledgement_thread
        self.mpu9250 = mpu9250
        self.measurement_thread_kwargs = measurement_thread_kwargs
        self.sockets = sockets
        self.package_num = 0  # For measurements_thread

    # @staticmethod
    def stop_measurements(self, measurements_thread):
        print('Trying to stop')
        if measurements_thread is None:
            print('measurements_thread is None, please initialize it beforehand')
        else:
            measurements_thread.stop_measurements()
            self.package_num = measurements_thread.package_num
            measurements_thread.join()
            print('Measurements thread is killed')

    # def get_measurements_thread(self, socket, response_address, mpu9250, measurement_thread_kwargs):
    #     measurements_thread = MeasurementsThread(
    #         socket,
    #         response_address,
    #         mpu9250,
    #         **measurement_thread_kwargs,
    #     )
    #
    #     return measurements_thread

    @staticmethod
    def time_sync(time_sync_source):
        print('Synchronizing time')
        os.system('sudo ntpdate ' + time_sync_source)

    def run(self):
        measurements_thread = None

        time_sync_source = 'ntp1.stratum1.ru'
        state = 'idle'
        msg_num_last = None

        while True:
            msg, addr = self.socket.recvfrom(1024)  # buffer size is 1024 bytes
            msg = msg.decode()
            print("received message:", msg)
            print("sender:", addr)
            # sender_ip = addr[0]
            # response_address = (sender_ip, self.UDP_PORT_SEND)

            msg_parts = msg.split(',')
            try:
                msg_num = int(msg_parts[0])
            except :
                print("Can't parse msg '" + msg + "'")
                continue

            # TODO: add acknownledgement responses
            if msg_num == 1:  # Reset
                ack_response_num = str(msg_num) if msg_num != msg_num_last else '0'
                self.acknowledgement_thread.send(ack_response_num + ',' + __version__)

                if (measurements_thread is not None) and measurements_thread.is_alive():
                    self.stop_measurements(measurements_thread)

                measurements_thread = None
                self.status_thread.periodic_sending = False
                self.time_thread.periodic_sending = False
                self.package_num = 0

                time_sync_source = 'ntp1.stratum1.ru'
                state = 'idle'
            elif msg_num == 2:  # Start
                ack_response_num = str(msg_num) if msg_num != msg_num_last else '0'
                self.acknowledgement_thread.send(ack_response_num)

                if (measurements_thread is not None) and measurements_thread.is_alive():
                    self.stop_measurements(measurements_thread)

                measurements_thread = MeasurementsThread(
                    self.sockets['client']['data'],  # It should be 'data' socket, right?  # Also should be simplified
                    self.addresses['server']['data'],
                    self.mpu9250,
                    # **self.measurement_thread_kwargs,
                    self.measurement_thread_kwargs,
                    package_num=self.package_num,
                )
                # measurements_thread = self.get_measurements_thread(
                #     socket=self.socket,
                #     response_address=self.addresses['server']['data'],
                #     mpu9250=self.mpu9250,
                #     measurement_thread_kwargs=self.measurement_thread_kwargs,
                # )
                # measurements_thread.stop = False
                # measurements_thread = get_measurements_thread()
                measurements_thread.start()
                self.status_thread.periodic_sending = True
                state = 'measuring'
                print('I am measuring')
            elif msg_num == 3:  # Stop
                ack_response_num = str(msg_num) if msg_num != msg_num_last else '0'
                self.acknowledgement_thread.send(ack_response_num)

                self.stop_measurements(measurements_thread)
                self.status_thread.periodic_sending = False
                state = 'idle'
            elif msg_num == 4:  # Time sync
                ack_response_num = str(msg_num) if msg_num != msg_num_last else '0'
                self.acknowledgement_thread.send(ack_response_num + ',0')

                thread = Thread(target=self.time_sync, args=(time_sync_source, ))
                thread.start()
            elif msg_num == 5:  # Time sync source
                ack_response_num = str(msg_num) if msg_num != msg_num_last else '0'
                self.acknowledgement_thread.send(ack_response_num)

                if len(msg_parts) >= 2:
                    new_time_sync_source = msg_parts[1]
                    try:
                        time_sync_source = str(new_time_sync_source)
                    except:
                        print('Fail to set the new time_sync_source')
            elif msg_num == 6:  # Start time sending
                ack_response_num = str(msg_num) if msg_num != msg_num_last else '0'
                self.acknowledgement_thread.send(ack_response_num)

                self.time_thread.periodic_sending = True

                # Double check because of name
            elif msg_num == 7:  # State
                ack_response_num = str(msg_num) if msg_num != msg_num_last else '0'
                self.acknowledgement_thread.send(ack_response_num + ',' + state)
                pass
            elif msg_num == 8:  # Send last measurement data
                ack_response_num = str(msg_num) if msg_num != msg_num_last else '0'
                self.acknowledgement_thread.send(ack_response_num)
                pass
            elif msg_num == 9:
                ack_response_num = str(msg_num) if msg_num != msg_num_last else '0'
                self.acknowledgement_thread.send(ack_response_num)

                if len(msg_parts) != 3:
                    print('Incorrect number of parts ' + str(len(msg_parts)))
                    continue

                ip_server_new = msg_parts[1]
                player_id_new = msg_parts[2]

                ports, addresses, sockets = get_ports_adresses_sockets(ip_server_new, ip_client, channels_dict, '07', player_id_new,
                                                                       get_server_sockets=False, get_client_sockets=False)

                self.status_thread.opponent_address = addresses['server']['status']
                self.time_thread.opponent_address = addresses['server']['time']
                self.acknowledgement_thread.opponent_address = addresses['server']['ack']

                if measurements_thread is not None:
                    # measurements_thread.socket = sockets['client']
                    measurements_thread.response_address = addresses['server']['data']

                self.addresses = addresses
                # self.sockets = sockets
                # self.socket = sockets['client']['cmd']


                # get_socket(ip_server, ports['server'][channel_name])  # Add for client too


            msg_num_last = msg_num