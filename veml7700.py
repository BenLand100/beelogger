from machine import I2C, Pin
import time

class VEML7700:
    
    # settings for [int_time_ms][gain]
    ALS_CONF_VALS = {  25: {1/8: bytearray([0x00, 0x13]), 1/4: bytearray([0x00,0x1B]), 1: bytearray([0x00, 0x01]), 2: bytearray([0x00, 0x0B])},
                       50: {1/8: bytearray([0x00, 0x12]), 1/4: bytearray([0x00,0x1A]), 1: bytearray([0x00, 0x02]), 2: bytearray([0x00, 0x0A])},
                       100:{1/8: bytearray([0x00, 0x10]), 1/4: bytearray([0x00,0x18]), 1: bytearray([0x00, 0x00]), 2: bytearray([0x00, 0x08])}, 
                       200:{1/8: bytearray([0x40, 0x10]), 1/4: bytearray([0x40,0x18]), 1: bytearray([0x40, 0x00]), 2: bytearray([0x40, 0x08])}, 
                       400:{1/8: bytearray([0x80, 0x10]), 1/4: bytearray([0x80,0x18]), 1: bytearray([0x80, 0x00]), 2: bytearray([0x80, 0x08])}, 
                       800:{1/8: bytearray([0xC0, 0x10]), 1/4: bytearray([0xC0,0x18]), 1: bytearray([0xC0, 0x00]), 2: bytearray([0xC0, 0x08])}} 

    # settings for [int_time_ms][gain]
    GAIN_VALS = {  25: {1/8: 1.8432, 1/4: 0.9216, 1: 0.2304, 2: 0.1152}, #25
                   50: {1/8: 0.9216, 1/4: 0.4608, 1: 0.1152, 2: 0.0576}, #50
                   100:{1/8: 0.4608, 1/4: 0.2304, 1: 0.0288, 2: 0.0144}, #100
                   200:{1/8: 0.2304, 1/4: 0.1152, 1: 0.0288, 2: 0.0144}, #200
                   400:{1/8: 0.1152, 1/4: 0.0576, 1: 0.0144, 2: 0.0072}, #400
                   800:{1/8: 0.0876, 1/4: 0.0288, 1: 0.0072, 2: 0.0036}} #800
    
    # Write registers
    ALS_CONF_0 = 0x00
    ALS_WH = 0x01
    ALS_WL = 0x02
    POW_SAV = 0x03

    # Read registers
    ALS = 0x04
    WHITE = 0x05
    INTERRUPT = 0x06

    def __init__(self, i2c, address=0x10):
       
        self.address = address
        self.i2c = i2c
        self.raw_lux = bytearray([0,0])

    def config(self, int_time_ms=25, gain=1/8):

        _conf = VEML7700.ALS_CONF_VALS.get(int_time_ms)
        _gain = VEML7700.GAIN_VALS.get(int_time_ms)
        if _conf is not None and _gain is not None:
            _conf = _conf.get(gain)
            _gain = _gain.get(gain)
            if _conf is not None and _gain is not None:
                self._conf = _conf
                self._gain = _gain
            else:
                raise ValueError('gain must be one of 1/8, 1/4, 1, or 2')
        else:
            raise ValueError('int_time_ms 25, 50, 100, 200, 400, or 800')
       
        self.i2c.writeto_mem(self.address, VEML7700.ALS_CONF_0, self._conf )
        
        defaults = bytearray([0x00, 0x00])
        self.i2c.writeto_mem(self.address, VEML7700.ALS_WH, defaults)
        self.i2c.writeto_mem(self.address, VEML7700.ALS_WL, defaults)
        self.i2c.writeto_mem(self.address, VEML7700.POW_SAV, defaults)
        
        #time.sleep_ms(40)
        
    def _measure(self):
        self.raw_lux = self.i2c.readfrom_mem(self.address, VEML7700.ALS, 2)
        
    def lux(self, read=True):
        if read: self._measure()
        return (self.raw_lux[0]+self.raw_lux[1]<<8)*self._gain