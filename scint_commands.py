import serial
import time
import sys

class scintillator():
    _voltageConversionFactor = 1.812e-3
    _currentConversionFactor = 4.98e-3
    _firstCoefficientConversionFactor = 5.225e-2
    _secondCoefficientConversionFactor = 1.507e-3
    @classmethod
    def _temperatureConversionFunction(cls, x):
        return (x * 1.907e-5 - 1.035) / (-5.5e-3)
    
    @classmethod
    def bytes_to_string(cls, byte_list):
        try:
            string = b''.join(byte_list).decode("ascii")
            return string
        except Exception as e:
            print(f"Error converting bytes to string: {e}")
            return None
    @classmethod
    def separate_byte_string(cls, input_bytes):
        separated_bytes = [input_bytes[i:i+4] for i in range(0, len(input_bytes), 4)]
        return separated_bytes
    
    def __init__(self, scint_number = 1, serial_port = "/dev/ttyUSB0", baud_rate = 9600):
        self.ser = serial.Serial(serial_port, baud_rate)
        self.scint = scint_number
    
    
    def sendCommand(self, command):
        #sends a command over the serial interface and returns the response as a byte list.
        for char in command:
            self.ser.write(char.encode('ascii'))
            time.sleep(.01)

        response = []
        start_time=time.time()
        while(True):
            if self.ser.in_waiting>0:
                received_byte = self.ser.read()
                response.append(received_byte)
            if time.time()-start_time>=1:
                break
        return(response)
    
    def HVStatus(self, status):
        #Interprets the bytes returned by HPO to help give the HV status
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

    def getStatus(self):
        #Gets status of HV chip--voltages, temperatures, configuration settings
        response = self.sendCommand("pmt HPO\r")
        byte_string = b''.join(response[byte] for byte in range(99, len(response)-8))
        byte_list = scintillator.separate_byte_string(byte_string)
        data = [int(byte.decode("ascii"), 16) for byte in byte_list] #turning that list into ints
        assert len(data)==5
        status = self.HVStatus(data[0])
        vo_set = data[1] * scintillator._voltageConversionFactor
        vo_mon = data[2] * scintillator._voltageConversionFactor
        io_mon = data[3] * scintillator._currentConversionFactor
        T_mon = scintillator._temperatureConversionFunction(data[4])
        return {
            "status": status,
            "vo_set": vo_set,
            "vo_mon": vo_mon,
            "io_mon": io_mon,
            "T_mon": T_mon
        }
    def HV_On(self):
        #Turns HV on
        command = "pmt HON\r"
        self.sendCommand(command)
        return "High Voltage On!"
    
    def HV_Off(self):
        #Turns off HV
        command = "pmt HOF\r"
        self.sendCommand(command)
        return "High Voltage Off!"

    def set_HV(self, voltage):
        #Sets the High Voltage to any value between 40 and 60--the range that the MC accepts
        if voltage < 40 or voltage >60:
            raise ValueError("Voltage is not within the appropriate range! It should be between 40V and 60V.")
        converted_voltage = voltage / scintillator._voltageConversionFactor
        hex_string = hex(int(converted_voltage))[2:]  # Convert the integer to hex and remove the '0x' prefix
        command = "pmt HBV"+ hex_string+"\r"
        self.sendCommand(command)
        return "HV set to "+ str(voltage) +"V"

    def get_MC_status(self):
        command = "status\r"
        response = self.sendCommand(command)
        return "Microcontroller Status: " + scintillator.bytes_to_string(response[8:17])+ ", " + scintillator.bytes_to_string(response[19:27])

#    def lgsel(self, toggle):
#        #Turns on or off the low gain select option based on user input
#        if toggle not in (0,1):
#            raise ValueError("lgsel must be 0 or 1!")
#        command = "lgsel " + str(toggle) + "\r"
#        response = self.sendCommand(command)
#        byte_string = scintillator.bytes_to_string(response[9:18])
#        return byte_string

    def customCommand(self, command):
        #Type a custom command string to send over to the microcontroller.
        response = self.sendCommand(command + "\r")
        output = scintillator.bytes_to_string(response)
        return output

    def help(self):
        #Displays a help message.
        print(help(scintillator))
    
if __name__ == "__main__":
     # Check if an argument is provided
    if len(sys.argv) < 2:
        print("Please provide a range value as a command-line argument.")
        sys.exit(1)
    try:
        range_value = int(sys.argv[1])
    except ValueError:
        print("Invalid range value. Please provide a valid integer.")
        sys.exit(1)

    scintillators = {}  # Use a dictionary to store instances
    for i in range(range_value):
        instance_name = f"scint_{i+1}"
        instance = scintillator(scint_number = i+1)
        scintillators[instance_name] = instance  # Store instance in the dictionary
        print(f"Created instance: {instance_name}")

    import code
    code.interact(
        "Interactive Scintillator Control\nUse 'scint_[scint number]' objects for access, scint_[i].help() shows functions",
        local=scintillators)  # Use the dictionary as the local namespace
