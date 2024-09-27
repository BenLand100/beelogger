import time
from machine import Pin

class HX711:
    READ_A_128 = 1
    READ_A_64 = 2
    READ_B_32 = 3
    
    def __init__(self,  clk=15, dat=2, mode=READ_A_128, scale=0.00005, offset=245500, tare=0.0):
        '''
        This device does not have a nice interface, but rather a:
            clk(15) - gpio pin that controls the state and clocks out data on the
            dat(2) - gpio pin used as a serial output from the device
        The number of clock pulses set the configuration for the next measurement
            scale - grams per count of raw value
            offset - subtracted from raw value prior to unit conversion
            tare - subtracted after conversion to grams
        '''
        self.scale = scale
        self.offset = offset
        self.tare = tare
        self.clk = Pin(clk, Pin.OUT)
        self.dat = Pin(dat, Pin.IN)
        #reset
        self.clk.value(1)
        self.set_mode(mode)
        
    def set_mode(self, mode):
        assert mode > 0 and mode < 4, f'Number of mode pulses ({mode}) is invalid'
        self._mode = mode
        self._read()
        
    def weight(self, cycles=8, scale=None, offset=None, tare=None):
        '''
        Measure the weight with some number of averaging cycles.
        kwargs override object defaults if set
        '''
        if scale is None:
            scale = self.scale
        if tare is None:
            tare = self.tare
        if offset is None:
            offset = self.offset
        avg = 0
        for i in range(cycles):
            val = self._read()
            if val > 0x7fffff:
                val -= 0x1000000
            avg += val
        return (avg / cycles - offset) * scale - tare
        
    def _read(self):
        self.clk.value(1)
        time.sleep_ms(1)
        self.clk.value(0)
        time.sleep_ms(1)
        i = 0
        while self.dat.value():
            time.sleep_ms(1)
            i = i+1
            if i > 500:
                print('Read timed out')
                break
        val = 0
        for i in range(24):
            self.clk.value(1)
            self.clk.value(0)
            val = (val << 1) | self.dat.value()
        for i in range(self._mode):
            self.clk.value(1)
            self.clk.value(0)
        self.clk.value(1)
        return val
