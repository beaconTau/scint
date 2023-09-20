import serial

# Specify the serial port
serial_port = '/dev/ttyUSB0'

# Specify the baud rate and other settings as needed
baud_rate = 9600

# Open the serial port
ser = serial.Serial(serial_port, baud_rate)
print(ser)
print(f"Serial port {serial_port} opened successfully.")

response = []

for i in range(30):
    received_byte = ser.read()
    response.append(received_byte)

byte_string = ''.join(byte.decode() for byte in response)
print(byte_string)
print("Communication Ended")
ser.close()
print(f"Serial port {serial_port} closed successfully.")
