import serial
import codecs
import binascii
import time

ser = serial.Serial(
	port='/dev/tty.usbserial-14410',\
	baudrate=57600,
	parity=serial.PARITY_NONE,\
	stopbits=serial.STOPBITS_ONE,\
	bytesize=serial.EIGHTBITS,\
	timeout=0)
  
print("connected to: " + ser.portstr)

read_tag = []

ser.close()
ser.open()
while True:        
        line = ser.readline()
        if len(line) > 10:
                the_val = int.from_bytes(line, "big")
                tag = str(the_val)
                if tag not in read_tag:
                        read_tag.append(tag)
                        print(tag)
                        print("Current count: {}".format(len(read_tag)))
                        #print(read_tag)

#while 1:
        #data = ser.readline(17)
        #print(data)
        #data = str(binascii.hexlify(ser.read(17))
        #print(data)
        #if data != "":
        #   print("tag: {}".format(data[6:22]))
        #else:
        #print("no tag detected")
        #time.sleep(1)
                
#ser.close()
