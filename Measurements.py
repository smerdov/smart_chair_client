# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime
import sys
import time
import argparse
import time
import sys
# import joblib
import os


# sys.path.append('../')  # For FaBo9Axis_MPU9250
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
    parser.add_argument('--wait', type=float, default=0)
    args = parser.parse_args()
    args = vars(args)

    return args

def get_sleep_time():
    current_time = time.time()
    time2sleep = timestep_detect - current_time % timestep_detect

    return time2sleep

if __name__ == '__main__':
    import FaBo9Axis_MPU9250
    mpu9250 = FaBo9Axis_MPU9250.MPU9250()

    args = parse_args()

    timestep_detect = args['timestep_detect']  # timestep between measurements
    timestep_send = args['timestep_send']  #  timestep between sendings
    max_time = args['max_time']  # total time of measurement
    verbose = args['verbose']
    label = args['label']
    person_id = args['person_id']
    meta = args['meta']
    send_data = args['send_data']
    save_data = args['save_data']
    folder = args['folder']
    synchronize_time = args['synchronize_time']
    wait = args['wait']

    time.sleep(wait)

    batch_size = int(timestep_send / timestep_detect)  # Количество измерений в одной отправке
    n_batches = int(max_time / timestep_send)  # Количество отправок

    time_start = datetime.now().strftime(TIME_FORMAT)[:-3]

    if folder is None:
        folder = time_start

    os.mkdir('../data/' + folder)  # Here we will store data in batches
    prefix = '../data/' + folder + '/'
    data_header = ['datetime_now', 'acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z', 'mag_x', 'mag_y', 'mag_z']
    data_header2write = ','.join(data_header) + '\n'

    # It's time to synchronize time!
    # Maybe you should use 'sudo python' instead of 'python' when running the script because of this command
    if synchronize_time:
        os.system('sudo ntpdate ntp1.stratum1.ru')

    for n_batch in range(n_batches):

        results_list = []
        filename = prefix + str(n_batch) + '.csv'
        file = open(filename, 'w')
        file.write(data_header2write)

        for n_measurement in range(batch_size):
            data_accelerometer = mpu9250.readAccel()
            data_gyroscope = mpu9250.readGyro()
            # data_magnetometer = mpu9250.readMagnet()
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

            # result = {
            #     'datetime_now': datetime.now().isoformat(),
            #     'accel_x': data_accelerometer['x'],
            #     'accel_y': data_accelerometer['y'],
            #     'accel_z': data_accelerometer['z'],
            #     'gyro_x': data_gyroscope['x'],
            #     'gyro_y': data_gyroscope['y'],
            #     'gyro_z': data_gyroscope['z'],
            #     'mag_x': data_magnetometer['x'],
            #     'mag_y': data_magnetometer['y'],
            #     'mag_z': data_magnetometer['z'],
            # }

            # data2write = json.dumps(result) + '\n'
            data2write = ','.join(measurement_data) + '\n'
            file.write(data2write)

            if n_measurement != batch_size - 1:  # Because if n_measurement != batch_size - 1 we need to consider time for file.close()
                time2sleep = get_sleep_time()
                time.sleep(time2sleep)

        file.close()
        time2sleep = get_sleep_time()
        time.sleep(time2sleep)

    print('---------------------------')
    print('----End of measurements----')
    print('---------------------------')






