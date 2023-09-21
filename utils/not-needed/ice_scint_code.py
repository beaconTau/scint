import serial
import sys
import time

class CommandParsingException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ErrorResponseException(Exception):
    def __init__(self, code):
        self.code = code
        self.message = HighVoltageChip._errorCodes[code]

    def __str__(self):
        return "Error ({0}): {1}".format(self.code, self.message)


class HighVoltageChip:
    _dataSizes = {
        "hxx": 4,
        "hpo": 20,
        "hst": 24,
        "hrt": 24,
        "hof": 0,
        "hon": 0,
        "hcm": 0,
        "hre": 0,
        "hbv": 0,
        "hgt": 4,
        "hgv": 4,
        "hgc": 4,
        "hgs": 4,
        "hsc": 0,
        "hrc": 4
    }
    _errorCodes = {
        1: "UART Communication Error",
        2: "Timeout Error",
        3: "Syntax Error",
        4: "Checksum Error",
        5: "Command Error",
        6: "Parameter Error",
        7: "Parameter Size Error"
    }
    _voltageConversionFactor = 1.812e-3
    _currentConversionFactor = 4.98e-3
    _firstCoefficientConversionFactor = 5.225e-2
    _secondCoefficientConversionFactor = 1.507e-3

    @classmethod
    def _temperatureConversionFunction(cls, x):
        return (x * 1.907e-5 - 1.035) / (-5.5e-3)

    @classmethod
    def _reversetemperatureConversionFunction(cls, y):
        return (1.035 - 5.5e-3 * y) / (1.907e-5)

    @classmethod
    def _commandResponseSize(cls, cmd):
        return 8 + cls._dataSizes[cmd]

    @classmethod
    def _dataToHex(cls, data):
        out = []
        for offset in range(0, len(data), 4):
            num = data[offset:(offset + 4)]
            out.append(int(num, base=16))
        return out

    @classmethod
    def _intToBytes(cls, value):
        return "{0:04x}".format(value).encode("ASCII")

    def __init__(self, deviceFile="/dev/ttyUSB0", baud=9600):
        self._port = serial.Serial(deviceFile, baud, parity=serial.PARITY_EVEN)

    def __del(self):
        self._port.close()

    def _sendCommand(self, cmd, data):
        if isinstance(data, str):
            data = data.encode("ASCII")
        elif isinstance(data, list):
            data = b''.join(HighVoltageChip._intToBytes(v) for v in data)
        elif isinstance(data, int):
            data = HighVoltageChip._intToBytes(data)
        if not isinstance(data, bytes):
            raise ValueError("data parameter cannot be converted to bytes, nor is it binary data")
        responseCmd = cmd.lower()
        cmd = bytes(cmd, "ASCII")
        cmdLine = b'\x02' + cmd + data + b'\x03'
        check = "{0:02x}".format(sum(cmdLine) & 0xff).upper().encode("ASCII")
        cmdLine += check + b'\x0D'
        print(cmdLine)
        self._port.write(cmdLine)
        #time.sleep(0.1)

    def _getResponse(self):
        response = b""
        state = 0
        while True:
            b = self._port.read(1)
            print(b, response)
            response += b
            if state == 0 and b == b"\x02":
                state = 1
            if state == 1 and b == b"\x03":
                state = 2
            if state == 2 and b == b"\x0D":
                break
        if (
            response[0] != 0x02
            or response[-1] != 0x0D
            or response[-4] != 0x03
        ):
            raise CommandParsingException("Frame bytes did not match")
        try:
            cmd = response[1:4].decode("ASCII")
            cmd = cmd.lower() #!!My edit
            if len(response) != HighVoltageChip._commandResponseSize(cmd):
                raise CommandParsingException("Expected data size does not match received data size")
            data = response[4:-4]
            assert len(data) == HighVoltageChip._dataSizes[cmd]
            checkReceived = int(response[-3:-1], base=16)
            checkCalculated = sum(response[:-3]) & 0xff
            if checkCalculated != checkReceived:
                raise CommandParsingException("Checksum mismatch")
            return cmd, HighVoltageChip._dataToHex(data)
        except IndexError:
            raise CommandParsingException("Unexpected end of data")

    def getOutputVoltage(self):
        self._sendCommand("HGV", b"")
        cmd, data = self._getResponse()
        if cmd == "hxx":
            raise ErrorResponseException(data[0])
        assert(cmd == "hgv")
        return data[0] * HighVoltageChip._voltageConversionFactor

    def getOutputCurrent(self):
        self._sendCommand("HGC", b"")
        cmd, data = self._getResponse()
        if cmd == "hxx":
            raise ErrorResponseException(data[0])
        assert(cmd == "hgc")
        return data[0] * HighVoltageChip._currentConversionFactor

    def getTemperature(self):
        self._sendCommand("HGT", b"")
        cmd, data = self._getResponse()
        if cmd == "hxx":
            raise ErrorResponseException(data[0])
        assert(cmd == "hgt")
        return HighVoltageChip._temperatureConversionFunction(data[0])

    def getTemperatureCorrectionFactor(self):
        self._sendCommand("HRT", b"")
        cmd, data = self._getResponse()
        if cmd == "hxx":
            raise ErrorResponseException(data[0])
        assert(cmd == "hrt")
        dT1_sec = data[0] * HighVoltageChip._secondCoefficientConversionFactor
        dT2_sec = data[1] * HighVoltageChip._secondCoefficientConversionFactor
        dT1 = data[2] * HighVoltageChip._firstCoefficientConversionFactor
        dT2 = data[3] * HighVoltageChip._firstCoefficientConversionFactor
        vb = data[4] * HighVoltageChip._voltageConversionFactor
        tb = HighVoltageChip._temperatureConversionFunction(data[5])
        return {
            "dT1_sec": dT1_sec,
            "dT2_sec": dT2_sec,
            "dT1": dT1,
            "dT2": dT2,
            "Vb": vb,
            "Tb": tb
        }

    def setTemperatureCorrectionFactor(self, dT1_s, dT2_s, dT1, dT2, tb):
        vRef = int(self.getTemperatureCorrectionFactor().get("Vb") / HighVoltageChip._voltageConversionFactor)
        dTs_max = 0xfc18 * HighVoltageChip._secondCoefficientConversionFactor
        dTs_min = 0x03e8 * HighVoltageChip._secondCoefficientConversionFactor
        dT_max = 0xfff * HighVoltageChip._firstCoefficientConversionFactor
        tb_min = HighVoltageChip._temperatureConversionFunction(0x0000)
        tb_max = HighVoltageChip._temperatureConversionFunction(0xffff)

        if not 0 <= dT1 <= dT_max:
            raise ValueError("dT1 must be in range 0V - {0}V".format(dT_max))

        if not 0 <= dT2 <= dT_max:
            raise ValueError("dT2 must be in range 0V - {0}V".format(dT_max))

        if not dTs_min <= dT1_s <= dTs_max:
            raise ValueError("dT1_s must be in range {0}V - {1}V".format(dTs_min, dTs_max))

        if not dTs_min <= dT2_s <= dTs_max:
            raise ValueError("dT2_s must be in range {0}V - {1}V".format(dTs_min, dTs_max))

        if not tb_min <= tb <= tb_max:
            raise ValueError("Tb must be in range {0}V - {1}V".format(tb_min, tb_max))

        value_dT1_s = int(dT1_s / HighVoltageChip._secondCoefficientConversionFactor)
        value_dT2_s = int(dT2_s / HighVoltageChip._secondCoefficientConversionFactor)
        value_dT1 = int(dT1 / HighVoltageChip._firstCoefficientConversionFactor)
        value_dT2 = int(dT2 / HighVoltageChip._firstCoefficientConversionFactor)
        value_tb = int(HighVoltageChip._reversetemperatureConversionFunction(tb))
        value_vb = vRef

        self._sendCommand("HST", [value_dT1_s, value_dT2_s, value_dT1, value_dT2, value_vb, value_tb])
        cmd, data = self._getResponse()
        if cmd == "hxx":
            raise ErrorResponseException(data[0])
        assert(cmd == "hst")

    def getStatus(self):
        self._sendCommand("HGS", b"")
        cmd, data = self._getResponse()
        if cmd == "hxx":
            raise ErrorResponseException(data[0])
        assert(cmd == "hgs")
        status = data[0]
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

    def setHighVoltageOutput(self, on):
        if on:
            self._sendCommand("HON", b"")
            cmd, data = self._getResponse()
            if cmd == "hxx":
                raise ErrorResponseException(data[0])
            assert(cmd == "hon")
        else:
            self._sendCommand("HOF", b"")
            cmd, data = self._getResponse()
            if cmd == "hxx":
                raise ErrorResponseException(data[0])
            assert(cmd == "hof")

    def setTemperatureCompensationMode(self, enabled):
        if enabled:
            self._sendCommand("HCM", b"\x31")
            cmd, data = self._getResponse()
            if cmd == "hxx":
                raise ErrorResponseException(data[0])
            assert(cmd == "hcm")
        else:
            self._sendCommand("HCM", b"\x30")
            cmd, data = self._getResponse()
            if cmd == "hxx":
                raise ErrorResponseException(data[0])
            assert(cmd == "hcm")

    def resetPowersupply(self):
        self._sendCommand("HRE", b"")
        cmd, data = self._getResponse()
        if cmd == "hxx":
            raise ErrorResponseException(data[0])
        assert(cmd == "hre")

    def setReferenceVoltage(self, voltage):
        max_v = 0xffff * HighVoltageChip._voltageConversionFactor
        if not 0 <= voltage <= max_v:
            raise ValueError("Reference voltage must be in range 0V - {0}V".format(max_v))
        value = int(voltage / HighVoltageChip._voltageConversionFactor)
        self._sendCommand("HBV", value)
        cmd, data = self._getResponse()
        if cmd == "hxx":
            raise ErrorResponseException(data[0])
        assert(cmd == "hbv")

    def getMonitoringInfo(self):
        self._sendCommand("HPO", b"")
        cmd, data = self._getResponse()
        if cmd == "hxx":
            raise ErrorResponseException(data[0])
        assert(cmd == "hpo")
        status = data[0]
        vo_set = data[1] * HighVoltageChip._voltageConversionFactor
        vo_mon = data[2] * HighVoltageChip._voltageConversionFactor
        io_mon = data[3] * HighVoltageChip._currentConversionFactor
        T_mon = HighVoltageChip._temperatureConversionFunction(data[4])
        return {
            "status": status,
            "vo_set": vo_set,
            "vo_mon": vo_mon,
            "io_mon": io_mon,
            "T_mon": T_mon
        }

    def readPowerFunction(self):
        self._sendCommand("HSC", b"")
        cmd, data = self._getResponse()
        if cmd == "hxx":
            raise ErrorResponseException(data[0])
        assert(cmd == "hsc")
        status = data[0]
        if status == 3:
            statusOCP = "Automatic Restoration"
            statusOVC = "Effectiveness"
        elif status == 1:
            statusOCP = "Automatic Restoration"
            statusOVC = "Invalid"
        elif status == 2:
            statusOCP = "Not in use"
            statusOVC = "Effectiveness"
        elif status == 0:
            statusOCP = "Not in use"
            statusOVC = "Invalid"
        else:
            statusOCP = "Error in Response Data"
            statusOVC = "Error in Response Data"
        return {
            "Over Current Protection Function": statusOCP,
            "Output Voltage Control Function": statusOVC
        }

    def setOverCurrentProtection(self, on):
        rPF = self.readPowerFunction()
        if rPF.get("Output Voltage Control Function") == "Effectiveness":
            if on:
                self._sendCommand("HSC", 3)
                cmd, data = self._getResponse()
                if cmd == "hxx":
                    raise ErrorResponseException(data[0])
                assert(cmd == "hsc")
            else:
                self._sendCommand("HSC", 2)
                cmd, data = self._getResponse()
                if cmd == "hxx":
                    raise ErrorResponseException(data[0])
                assert(cmd == "hsc")
        elif rPF.get("Output Voltage Control Function") == "Invalid":
            if on:
                self._sendCommand("HSC", 1)
                cmd, data = self._getResponse()
                if cmd == "hxx":
                    raise ErrorResponseException(data[0])
                assert(cmd == "hsc")
            else:
                self._sendCommand("HSC", 0)
                cmd, data = self._getResponse()
                if cmd == "hxx":
                    raise ErrorResponseException(data[0])
                assert(cmd == "hsc")
        else:
            return {"Not able to get Output-Voltage-Control-Function Status"}

    def setOutputVoltageControlFunction(self, on):
        rPF = self.readPowerFunction()
        if rPF.get("Over Current Protection Function") == "Automatic Restoration":
            if on:
                self._sendCommand("HSC", 3)
                cmd, data = self._getResponse()
                if cmd == "hxx":
                    raise ErrorResponseException(data[0])
                assert(cmd == "hsc")
            else:
                self._sendCommand("HSC", 1)
                cmd, data = self._getResponse()
                if cmd == "hxx":
                    raise ErrorResponseException(data[0])
                assert(cmd == "hsc")
        elif rPF.get("Over Current Protection Function") == "Not in use":
            if on:
                self._sendCommand("HSC", 2)
                cmd, data = self._getResponse()
                if cmd == "hxx":
                    raise ErrorResponseException(data[0])
                assert(cmd == "hsc")
            else:
                self._sendCommand("HSC", 0)
                cmd, data = self._getResponse()
                if cmd == "hxx":
                    raise ErrorResponseException(data[0])
                assert(cmd == "hsc")
        else:
            return {"Not able to get Over-Current-Protection-Function Status"}
        
    def setOutputVoltageControlFunction(self, on):
        "Set Output Voltage Control Function"
        rPF = readPowerFunction(self)  # Looks whether Over Current Protection is set or not
        if rPF.get("Over Current Protection Function") == "Automatic Restoration":
            if on:
                self._sendCommand("HSC", 3)
                cmd, data = self._getResponse()
                if cmd == "hxx":
                    raise ErrorResponseException(data[0])
                assert(cmd == "hsc")
            else:
                self._sendCommand("HSC", 1)
                cmd, data = self._getResponse()
                if cmd == "hxx":
                    raise ErrorResponseException(data[0])
                assert(cmd == "hsc")
        elif rPF.get("Over Current Protection Function") == "Not in use":
            if on:
                self._sendCommand("HSC", 2)
                cmd, data = self._getResponse()
                if cmd == "hxx":
                    raise ErrorResponseException(data[0])
                assert(cmd == "hsc")
            else:
                self._sendCommand("HSC", 0)
                cmd, data = self._getResponse()
                if cmd == "hxx":
                    raise ErrorResponseException(data[0])
                assert(cmd == "hsc")
        else:
            return {"Not able to get Over-Current-Protection-Function Status"}

    def help(self):
        "Displays a help message."
        print(help(HighVoltageChip))

if __name__ == "__main__":
    try:
        deviceFile = sys.argv[1]
    except IndexError:
        deviceFile = "/dev/ttyUSB0"
    hvc = HighVoltageChip(deviceFile)
    
    print(hvc.getTemperature())
    print(hvc.getStatus())
    print(hvc.getMonitoringInfo()["vo_mon"])
    #hvc.setReferenceVoltage(65.0)
    #print(hvc.getMonitoringInfo()["vo_mon"])
    #import code
    #code.interact(
        #"Interactive Powersupply Control\nUse 'hvc' object for access, hvc.help() shows functions",
        #local={"hvc": hvc}
    #)
