import socket
import Measurements
from Measurements import TIME_FORMAT
from threading import Thread
import datetime

# UDP_IP = "10.1.30.36"
UDP_IP = "192.168.43.154"


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
        repr = self.__class__.__name__ + '__' + super().__repr__() + '__' + str(self.get_response())
        return repr

    def get_response(self):
        response_values = []

        for key in self.key_order:
            value2append = self.info_dict.get(key, '')
            response_values.append(value2append)

        response = ','.join(response_values)

        return response

    def run(self):
        while True:
            msg, addr = self.socket_receiver.recvfrom(1024)  # buffer size is 1024 bytes
            msg = msg.decode()
            print("received message:", msg)
            print("sender:", addr)
            sender_ip = addr[0]
            response_address = (sender_ip, self.UDP_PORT_SEND)

            response_msg = self.get_response()
            self.socket_receiver.sendto(response_msg, response_address)


status_thread = StatusThread(
    UDP_IP=UDP_IP,
    channel='1',
    sensor_type='07',
    player='1',
)

status_thread['version'] = Measurements.__version__  # Has to be checked
status_thread['sensor_name'] = 'smartchair'
status_thread['support_cmd'] = '1'
status_thread['status'] = 'ok'

status_thread.start()


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

            response_msg = datetime.datetime.now().strftime(TIME_FORMAT)[:-3]
            self.socket_receiver.sendto(response_msg, response_address)

    def __repr__(self):
        repr = self.__class__.__name__ + '__' + super().__repr__()
        return repr



time_thread = TimeThread(
    UDP_IP=UDP_IP,
    channel='2',
    sensor_type='07',
    player='1',
)





