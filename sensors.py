from machine import Pin, I2C
from bmp180 import BMP180
from i2cmux import I2CMUX
from aht10 import AHT10
from veml7700 import VEML7700
from hx711 import HX711
import time

class Sensors:
    
    def __init__(self, i2c, spi, weight_pins=None, bmp180=False, veml7700=False, aht10=0):
        '''
        Abstraction of the sensor platform.
            i2c - a micropython I2C or SoftI2C object as the i2c bus
            spi - a micropython SPI or SoftSPI object as the spi bus
            weight_pins - a tuple of (clk,dat) gpio pin numbers fir weight sensor
        '''
        self.i2c = i2c
        
        init_log = []
        
        try:
            self.switch = I2CMUX(self.i2c)
            self.switch.set_state(bus=0)
        except:
            init_log.append('Could not init i2c switch')
        
        if bmp180:
            try:
                self.bmp = BMP180(self.i2c)
                self.bmp.config()
            except:
                self.bmp = None
                init_log.append('Failed to initialize bmp180 barometer')
        else:
            self.bmp = None        
        
        if veml7700:
            try:
                self.veml = VEML7700(self.i2c)
                self.veml.config()
            except:
                self.bmp = None
                init_log.append('Failed to initialize veml7700 ambient light sensor')
        else:
            self.veml = None
            
        self.ahts = []
        for i in range(aht10):
            try:
                self.switch.set_state(bus=i)
                aht = AHT10(self.i2c)
                aht.config()
                self.ahts.append(aht)
            except:
                init_log.append(f'Failed to initialize aht10-{i} temperature/humidity sensor')
                self.ahts.append(None)
        
        if weight_pins is not None:
            try:
                assert len(weight_pins) == 2, 'weight_pins must specify (clk,dat) lines for hx711'
                self.weight = HX711(clk=weight_pins[0],dat=weight_pins[1])
            except:
                self.bmp = None
                init_log.append('Failed to initialize hx711 weight sensor')
        else:
            self.weight = None

        self.init_issues = init_log
            
    def __str__(self):
        info = 'Sensor readings:'
        for key,val in self.report().items():
            unit = self.report_unit(key)
            info += f'\n  {key} = {val} {unit}'
        return info
    
    def report_unit(self, key):
        if 'temperature' in key:
            unit = 'C'
        elif 'pressure' in key:
            unit = 'kPa'
        elif 'altitude' in key:
            unit = 'm'
        elif 'humidity' in key:
            unit = '%'
        elif 'weight' in key:
            unit = 'kg'
        else:
            unit = ''
        return unit
    
    def report(self):
        lux = self.read_lux()
        ext_temp,ext_press = self.read_temp_pressure()
        
        report = {
            'ambient_lux': lux,
            'ext_temperature': ext_temp,
            'ext_pressure': ext_press
        }
        for i,(temp,humid) in enumerate(self.read_all_temp_humid()):
            report[f'temperature_{i}'] = temp
            report[f'humidity_{i}'] = humid
            
        report['weight'] = self.read_weight()
        return report        
    
    def read_weight(self):
        try:
            return self.weight.weight()
        except:
            return None
    
    def read_lux(self):
        try:
            self.switch.set_state(bus=0)
            lux = self.veml.lux()
            return lux
        except:
            return None
            
    def read_temp_pressure(self):
        try:
            self.switch.set_state(bus=0)
            temp = self.bmp.temperature()
            pressure = self.bmp.pressure(read=False)
            return temp, pressure/1000.0
        except:
            return None, None
        
    def read_temp_humid(self, idx):
        try:
            self.switch.set_state(bus=idx)
            return self.ahts[idx].both()
        except:
            return (None,None)
            
    def read_all_temp_humid(self):
        results = []
        for i in range(len(self.ahts)):
            result = self.read_temp_humid(i)
            results.append(result)
        return results