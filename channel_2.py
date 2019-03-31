import socket
import datetime
from threading import Thread

TIME_FORMAT = '%H:%M:%S.%f'

thread = Thread()
thread.start()

# UDP_IP = "10.1.30.36"
UDP_IP = "192.168.43.154"

channel_num = '2'
sensor_type_num = '07'
player_num = '0'

def get_server_client_ports(channel_num, sensor_type_num, player_num):
    port_server = '6' + channel_num + sensor_type_num + player_num
    port_client = '60'+ channel_num + sensor_type_num

    return int(port_server), int(port_client)

port_server, port_client = get_server_client_ports(channel_num, sensor_type_num, player_num)

UDP_PORT_RECEIVE = port_client
UDP_PORT_SEND = port_server

socket_receiver = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
socket_receiver.bind((UDP_IP, UDP_PORT_RECEIVE))

while True:
    msg, addr = socket_receiver.recvfrom(1024) # buffer size is 1024 bytes
    msg = msg.decode()
    print ("received message:", msg)
    print ("sender:", addr)
    sender_ip = addr[0]
    response_address = (sender_ip, UDP_PORT_SEND)

    response_msg = datetime.datetime.now().strftime(TIME_FORMAT)[:-3]

    socket_receiver.sendto(response_msg, response_address)













