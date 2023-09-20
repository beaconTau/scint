import serial
import time

def bytes_to_string(byte_list):
    try:
        string = b''.join(byte_list).decode("utf-8")
        return string
    except Exception as e:
        print(f"Error converting bytes to string: {e}")
        return None
    
def separate_byte_string(input_bytes):
    separated_bytes = [input_bytes[i:i+4] for i in range(0, len(input_bytes), 4)]
    return separated_bytes


def temperatureConversionFunction(x):
        return (x * 1.907e-5 - 1.035) / (-5.5e-3)
    
def getStatus(status):
    high_voltage = (status & 1) != 0
    overcurrent_protection = (status & 2) != 0
    current_in_specification = (status & 4) == 0
    sensor_connected = (status & 8) == 0
    sensor_in_specification = (status & 16) == 0
    temp_conv_ef = (status & 64) == 0
    return {
        "high_voltage_on": high_voltage,
        "overcurrent_protection": overcurrent_protection,
        "current_in_specification": current_in_specification,
        "sensor_connected": sensor_connected,
        "sensor_in_specification": sensor_in_specification,
        "temperature_conversion_effective": temp_conv_ef
    }

def getHPO(response):
    byte_string = b''.join(response[byte] for byte in range(99, len(response)-8))
    byte_list = separate_byte_string(byte_string)
    data = [int(byte.decode("ascii"), 16) for byte in byte_list] #turning that list into ints
    assert len(data)==5
    status = getStatus(data[0])
    vo_set = data[1] * voltageConversionFactor
    vo_mon = data[2] * voltageConversionFactor
    io_mon = data[3] * currentConversionFactor
    T_mon = temperatureConversionFunction(data[4])
    return {
        "status": status,
        "vo_set": vo_set,
        "vo_mon": vo_mon,
        "io_mon": io_mon,
        "T_mon": T_mon
        }

def commandHandler(command, response):
    if command == "pmt HPO\r":
       return getHPO(response)
    if command == "pmt HON\r":
        return "High Voltage On!"
    if command == "pmt HOF\r":
        return "High Voltage Off!"
    if command == "status\r":
        return bytes_to_string(response[8:17])+", " +bytes_to_string(response[19:27])
    if command[0:7] == "pmt HBV":
        return "High Voltage Set!"
if __name__ == "__main__":
    # Specify the serial port
    serial_port = '/dev/ttyUSB0'
    
    #specify conversion factors
    voltageConversionFactor = 1.812e-3
    currentConversionFactor = 4.98e-3
    firstCoefficientConversionFactor = 5.225e-2
    secondCoefficientConversionFactor = 1.507e-3 
    
    # Specify the baud rate and other settings as needed
    baud_rate = 9600
    
    # Open the serial port
    ser = serial.Serial(serial_port, baud_rate)
    command = input("Enter Command Here: ")
    command += "\r"
    print(f"Serial port {serial_port} opened successfully.")
    for char in command:
        ser.write(char.encode('ascii'))
        time.sleep(.01)


    response = []
    start_time=time.time()
    while(True):
        if ser.in_waiting>0:
            received_byte = ser.read()
            response.append(received_byte)
        if time.time()-start_time>=1:
            break
        
    print(response[9:16])
    print(commandHandler(command, response))
    print("Communication Ended")
    ser.close()
    print(f"Serial port {serial_port} closed successfully.")




