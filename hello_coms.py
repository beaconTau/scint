import serial
import time

# Specify the serial port
serial_port = '/dev/ttyUSB0'

# Specify the baud rate and other settings as needed
baud_rate = 9600

# Open the serial port
ser = serial.Serial(serial_port, baud_rate)
print(f"Serial port {serial_port} opened successfully.")
command = input("Enter Command here: ")
command += "\r"
for char in command:
    ser.write(char.encode('ascii'))
    time.sleep(.01)
    
    
response = []
start_time=time.time()
while(True):
    if ser.in_waiting>0:
        received_byte = ser.read()
        response.append(received_byte)
        if received_byte == b"\r":
            byte_string = ''.join(byte.decode() for byte in response)
            print(byte_string)
            response = []
    if time.time()-start_time>=1:
        byte_string = ''.join(byte.decode() for byte in response)
        break
print("Communication Ended")
ser.close()
print(f"Serial port {serial_port} closed successfully.")
