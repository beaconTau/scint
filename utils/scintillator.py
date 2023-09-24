"""This file defines the Scintillator class holding immediate commands to the scintillator"""
from serial import Serial
import time

class Scintillator():

    # private attributes to all instances
    _voltageConversionFactor = 1.812e-3
    _currentConversionFactor = 4.98e-3
    _firstCoefficientConversionFactor = 5.225e-2
    _secondCoefficientConversionFactor = 1.507e-3
    
    def __init__(self, scint_number = 1, serial_port = None, baud_rate = 9600):

        self.scint_channel = scint_number

        if serial_port is None:     # if not given, assume by-id method
            serial_id = f"usb-FTDI_USB-COM485_Plus4_FT4J7CE9-if0{int(scint_number-1)}-port0"
            serial_port = f"/dev/serial/by-id/{serial_id}"
        self.port = serial_port
        self.ser = Serial(serial_port, baud_rate)

    
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
        """Get the status dict of HV chip--voltages, temperatures, configuration settings"""
        response = self.sendCommand("pmt HPO\r")
        byte_string = b''.join(response[byte] for byte in range(99, len(response)-8))
        byte_list = self._separate_byte_string(byte_string)
        data = [int(byte.decode("ascii"), 16) for byte in byte_list] #turning that list into ints
        if len(data)==5:
            HVstatus = self.HVStatus(data[0])
            vo_set = data[1] * Scintillator._voltageConversionFactor
            vo_mon = data[2] * Scintillator._voltageConversionFactor
            io_mon = data[3] * Scintillator._currentConversionFactor
            T_mon = self._temperatureConversionFunction(data[4])
        else:
            print(f"Warning: Scintillator channel {self.scint_channel} not detected")
            HVstatus = self.HVStatus(0)
            for key in HVstatus:
                HVstatus[key] = -1
            vo_set = -1
            vo_mon = -1
            io_mon = -1
            T_mon = -1
        status_dict = {
            "channel": self.scint_channel,
            "serial port": self.port,
            **HVstatus,
            "vo_set": vo_set,
            "vo_mon": vo_mon,
            "io_mon": io_mon,
            "T_mon": T_mon
        }
        return status_dict
    
    def printStatus(self):
        """Give a nice print message outlining the status"""
        status_dict = self.getStatus()
        status_msg = ""
        for key in status_dict:
            status_msg += f"{key} -- {status_dict[key]}\n"
        print(status_msg)
    
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
        converted_voltage = voltage / Scintillator._voltageConversionFactor
        hex_string = hex(int(converted_voltage))[2:]  # Convert the integer to hex and remove the '0x' prefix
        command = "pmt HBV"+ hex_string+"\r"
        self.sendCommand(command)
        return "HV set to "+ str(voltage) +"V"

    def get_MC_status(self):
        command = "status\r"
        response = self.sendCommand(command)
        return "Microcontroller Status: " + self._bytes_to_string(response[8:17])+ ", " + self._bytes_to_string(response[19:27])

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
        output = self._bytes_to_string(response)
        return output

    def help(self):
        #Displays a help message.
        print(help(Scintillator))


    # -- private methods --

    def _temperatureConversionFunction(self, x):
        return (x * 1.907e-5 - 1.035) / (-5.5e-3)
    
    def _bytes_to_string(self, byte_list):
        try:
            string = b''.join(byte_list).decode("ascii")
            return string
        except Exception as e:
            print(f"Error converting bytes to string: {e}")
            return None
    
    def _separate_byte_string(self, input_bytes):
        separated_bytes = [input_bytes[i:i+4] for i in range(0, len(input_bytes), 4)]
        return separated_bytes