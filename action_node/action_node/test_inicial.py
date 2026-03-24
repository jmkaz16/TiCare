import serial
import time

ser = serial.Serial('/dev/rfcomm0', 115200, timeout=1)

time.sleep(2)
ser.write(b'kup\n')

time.sleep(2)
ser.write(b'ksit\n') #la b es para indicar que 'ksit' es una secuencia de bytes

time.sleep(2)
ser.write(b'kbalance\n')

time.sleep(2)
ser.write(b'kwkF\n')

time.sleep(2)
ser.write(b'd\n')

time.sleep(3)

ser.close()