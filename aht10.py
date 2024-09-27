import time

class AHT10:
    #AHT10 commands are REG VALUE NOP where NOPs are 0x00
    #CMD_INITIALIZE = bytearray([0xE1, 0x00, 0x00]) # Normal mode
    CMD_INITIALIZE = bytearray([0xE1, 0x08, 0x00]) # Calibration ON, Normal mode
    CMD_MEASURE = bytearray([0xAC, 0x33, 0x00]) # Docs claim 0x33 is related to ADC
    STATUS_BUSY = 0x80  # Status bit for busy
    STATUS_CALIBRATED = 0x08  # Status bit for calibrated
    
    def __init__(self, i2c, address=0x38, offset=0): #or 0x39 with a resistor mod
        self.i2c = i2c
        self.address = address
        self.data = bytearray(6)
        self.raw_temp = 0
        self.raw_humid = 0
        self.raw_status = 0
        self.offset = offset-50
        
    def config(self):
        self.i2c.writeto(self.address, AHT10.CMD_INITIALIZE)

    def _status(self):
        self.raw_status = self.i2c.readfrom(self.address, 1)
    
    def _measure(self):
        self.i2c.writeto(self.address, AHT10.CMD_MEASURE)
        time.sleep_ms(75)
        self.i2c.readfrom_into(self.address, self.data) # Might be better to loop than wait and hope
        assert (self.data[0] & AHT10.STATUS_BUSY) == 0, 'Device was busy'
        assert (self.data[0] & AHT10.STATUS_CALIBRATED) != 0, 'Device not calibrated'
        self.raw_humid = self.data[1] << 12 | self.data[2] << 4 | self.data[3] >> 4
        self.raw_temp = (self.data[3] & 0x0F) << 16 | self.data[4] << 8 | self.data[5]
        
    def both(self, read=True):
        if read: self._measure()
        return self.temperature(read=False), self.humidity(read=False)

    def humidity(self, read=True):
        if read: self._measure()
        return (self.raw_humid / 2**20) * 100 

    def temperature(self, read=True):
        if read: self._measure()
        return (self.raw_temp / 2**20) * 200 + self.offset

    def dew_point(self, read=True):
        t,h = self.both(read=read)
        h = (log(h, 10) - 2) / 0.4343 + (17.62 * t) / (243.12 + t)
        return 243.12 * h / (17.62 - h)