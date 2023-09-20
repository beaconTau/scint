import serial
import time
# Open the serial communication on COM10
ser = serial.Serial('/dev/ttyUSB1', baudrate=9600)
ser2 = serial.Serial('/dev/ttyUSB0', baudrate=9600)
message=b'/xE8'

while(True):
# Send the command over the serial communication
    ser.write(message)
    response=b""
    for i in range(4):
        response+=ser2.read()
    print("response:")
    print(response)
    if response==message:
        ser2.write(message)
        response2 =b""
        for i in range(4):
            response2+=ser.read()
        print("response 2:")
        print(response2)
        if response2==message:
            print("Communication Achieved")
            break
    time.sleep(.1)
ser.close()
ser2.close()
