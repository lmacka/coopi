import time
from GreenPonik_BH1750.BH1750 import BH1750
import os
import glob

def read_cpu_temperature():
    try:
        base_dir = '/sys/class/thermal/thermal_zone0/'
        file_path = glob.glob(base_dir + 'temp')[0]
        with open(file_path, 'r') as file:
            temp = float(file.read()) / 1000
        return temp
    except Exception as e:
        print('An exception occurred: {}'.format(e))
        return None

def read_light_sensor():
    try:
        bh = BH1750()
        lux = bh.read_bh1750()
        return(lux)
    except Exception as e:
        print('An exception occurred: {}'.format(e))
        return None

if __name__ == "__main__":
    while True:
        print("Light level: ", read_light_sensor(),"lux")
        print("CPU temperature: ", read_cpu_temperature())
        time.sleep(1)