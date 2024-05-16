import time
from GreenPonik_BH1750.BH1750 import BH1750
import glob
import DHT
import pigpio

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

def read_dht():
    # Sensor should be set to DHT.DHT11, DHT.DHTXX or DHT.DHTAUTO
    sensor = DHT.DHTXX

    pin = 22     # Data - Pin 3 (BCM 22)

    def output_data(timestamp, temperature, humidity):
        # Sample output Date: 2019-11-17T10:55:08, Temperature: 25°C, Humidity: 72%
        date = datetime.datetime.fromtimestamp(timestamp).replace(microsecond=0).isoformat()
        print(u"Date: {:s}, Temperature: {:g}\u00b0C, Humidity: {:g}%".format(date, temperature, humidity))

    pi = pigpio.pi()
    if not pi.connected:
        return 'Error connecting to piGPIO'

    s = DHT.sensor(pi, pin, model = sensor)

    tries = 5   # try 5 times if error
    while tries:
        try:
            timestamp, gpio, status, temperature, humidity = s.read()   #read DHT device
            if(status == DHT.DHT_TIMEOUT):  # no response from sensor
                exit()
            if(status == DHT.DHT_GOOD):
                output_data(timestamp, temperature, humidity)
                exit()      # Exit after successful read
            time.sleep(2)
            tries -=1
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    while True:
        print("Light level: ", read_light_sensor(),"lux")
        print("CPU temperature: ", read_cpu_temperature())
        temperature, humidity = read_dht()
        time.sleep(1)