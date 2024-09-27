from ustruct import unpack as unp
from machine import I2C, Pin
import math
import time

class BMP180():
    
    def __init__(self, i2c, address=0x77):

        self.address = address
        self.i2c = i2c
        
        self.oversample_setting = 3 # 0,1,2,3
        self.baseline = 101325.0 # pressure at altitude of zero

        # output raw
        self.UT_raw = None
        self.B5_raw = None
        self.MSB_raw = None
        self.LSB_raw = None
        self.XLSB_raw = None
        self._measure_iter = self._measure()
        
            
    def config(self):
        self.chip_id = self.i2c.readfrom_mem(self.address, 0xD0, 2)
        # read calibration data from EEPROM
        self._AC1 = unp('>h', self.i2c.readfrom_mem(self.address, 0xAA, 2))[0]
        self._AC2 = unp('>h', self.i2c.readfrom_mem(self.address, 0xAC, 2))[0]
        self._AC3 = unp('>h', self.i2c.readfrom_mem(self.address, 0xAE, 2))[0]
        self._AC4 = unp('>H', self.i2c.readfrom_mem(self.address, 0xB0, 2))[0]
        self._AC5 = unp('>H', self.i2c.readfrom_mem(self.address, 0xB2, 2))[0]
        self._AC6 = unp('>H', self.i2c.readfrom_mem(self.address, 0xB4, 2))[0]
        self._B1 = unp('>h', self.i2c.readfrom_mem(self.address, 0xB6, 2))[0]
        self._B2 = unp('>h', self.i2c.readfrom_mem(self.address, 0xB8, 2))[0]
        self._MB = unp('>h', self.i2c.readfrom_mem(self.address, 0xBA, 2))[0]
        self._MC = unp('>h', self.i2c.readfrom_mem(self.address, 0xBC, 2))[0]
        self._MD = unp('>h', self.i2c.readfrom_mem(self.address, 0xBE, 2))[0]
        
        for _ in range(128):
            next(self._measure_iter)
            time.sleep_ms(1)
        
    
    
    def calibration(self):
        '''
        Returns a list of all compensation values
        '''
        return [self._AC1, self._AC2, self._AC3, self._AC4, self._AC5, self._AC6, 
                self._B1, self._B2, self._MB, self._MC, self._MD, self.oversample_setting]

    def _measure(self):
        '''
        Generator refreshing the raw measurments.
        '''
        delays = (5, 8, 14, 25)
        while True:
            self.i2c.writeto_mem(self.address, 0xF4, bytearray([0x2E]))
            t_start = time.ticks_ms()
            while (time.ticks_ms() - t_start) <= 5: # 5mS delay
                yield None
            try:
                self.UT_raw = self.i2c.readfrom_mem(self.address, 0xF6, 2)
            except:
                yield None
            self.i2c.writeto_mem(self.address, 0xF4, bytearray([0x34+(self.oversample_setting << 6)]))
            t_pressure_ready = delays[self.oversample_setting]
            t_start = time.ticks_ms()
            while (time.ticks_ms() - t_start) <= t_pressure_ready:
                yield None
            try:
                self.MSB_raw = self.i2c.readfrom_mem(self.address, 0xF6, 1)
                self.LSB_raw = self.i2c.readfrom_mem(self.address, 0xF7, 1)
                self.XLSB_raw = self.i2c.readfrom_mem(self.address, 0xF8, 1)
            except:
                yield None
            yield True
            
    def temperature(self, read=True):
        '''
        Temperature in degree C.
        '''
        if read: next(self._measure_iter)
        try:
            UT = unp('>H', self.UT_raw)[0]
        except:
            return 0.0
        X1 = (UT-self._AC6)*self._AC5/2**15
        X2 = self._MC*2**11/(X1+self._MD)
        self.B5_raw = X1+X2
        return (((X1+X2)+8)/2**4)/10

    def pressure(self, read=True):
        '''
        Pressure in mbar.
        '''
        if read: self.temperature(read=read)  # Populate self.B5_raw
        try:
            MSB = unp('B', self.MSB_raw)[0]
            LSB = unp('B', self.LSB_raw)[0]
            XLSB = unp('B', self.XLSB_raw)[0]
        except:
            return 0.0
        UP = ((MSB << 16)+(LSB << 8)+XLSB) >> (8-self.oversample_setting)
        B6 = self.B5_raw-4000
        X1 = (self._B2*(B6**2/2**12))/2**11
        X2 = self._AC2*B6/2**11
        X3 = X1+X2
        B3 = ((int((self._AC1*4+X3)) << self.oversample_setting)+2)/4
        X1 = self._AC3*B6/2**13
        X2 = (self._B1*(B6**2/2**12))/2**16
        X3 = ((X1+X2)+2)/2**2
        B4 = abs(self._AC4)*(X3+32768)/2**15
        B7 = (abs(UP)-B3) * (50000 >> self.oversample_setting)
        if B7 < 0x80000000:
            pressure = (B7*2)/B4
        else:
            pressure = (B7/B4)*2
        X1 = (pressure/2**8)**2
        X1 = (X1*3038)/2**16
        X2 = (-7357*pressure)/2**16
        return pressure+(X1+X2+3791)/2**4

    def altitude(self, read=True):
        '''
        Altitude in m.
        '''
        try:
            p = -7990.0*math.log(self.pressure(read=read)/self.baseline)
        except:
            p = 0.0
        return p