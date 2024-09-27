class I2CMUX:
    
    def __init__(self, i2c, address=0x70): #three bits to play with for address
        self.i2c = i2c
        self.address = address
        
    def get_state(self):
        return self.i2c.readfrom(self.address, 1)
    
    def set_state(self, mask=None, bus=None, zero=False, one=False, two=False, three=False, four=False, five=False, six=False, seven=False):
        if bus is not None:
            mask = 2**bus
        elif mask is None:
            mask = (2**0 if zero else 0)|(2**1 if one else 0)|(2**2 if two else 0)|(2**3 if three else 0)|(2**4 if four else 0)|(2**5 if five else 0)|(2**6 if six else 0)|(2**7 if seven else 0)
        self.i2c.writeto(self.address, bytearray([mask]))