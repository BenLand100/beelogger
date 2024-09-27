import machine
import network
from machine import SoftI2C, SoftSPI, Pin

try: # webrepl gets unhappy if the whole thing unwinds
    
    
    from server import JSONServer
    from sensors import Sensors
    from ili9341 import ILI9341, color565, fcolor565

    lan = network.LAN(
        mdc = machine.Pin(23),
        mdio = machine.Pin(18),
        power = machine.Pin(12),
        phy_type = network.PHY_LAN8720,
        phy_addr = 0
    )
    print('LAN:',lan.active(1))
    lan.ifconfig(
        #('192.168.42.2',
        # '255.255.255.0',
        # '192.168.42.1',
        # '8.8.8.8')
    )

    spi = SoftSPI(baudrate=200000, sck=Pin(14), mosi=Pin(2), miso=Pin(15))
    i2c = SoftI2C(scl=Pin(16), sda=Pin(13), freq=100000)
    weight_pins = (4, 36) # (clk, dat)
    TOTAL_AHT10 = 5
    sensors = Sensors(i2c, spi, weight_pins=weight_pins, bmp180=True, veml7700=True, aht10=TOTAL_AHT10)
    
    if len(sensors.init_issues) > 0:
        print('\n'.join(sensors.init_issues))
        
    server = JSONServer()

    def handle_hello(req):
        req.reply(msg='hello')
    server.add_endpoint('GET', '/hello', handle_hello)

    def handle_report(req):
        try:
            report = sensors.report()
            req.reply(**report)
        except Exception as e:
            req.error(str(e), code=500)
    server.add_endpoint('GET', '/report', handle_report)
    
    def handle_lux(req):
        try:
            lux = sensors.read_lux()
            req.reply(ambient_lux=lux)
        except Exception as e:
            req.error(str(e), code=500)
    server.add_endpoint('GET', '/lux', handle_lux)
    
    def handle_weight(req):
        try:
            weight = sensors.read_weight()
            req.reply(weight=weight)
        except Exception as e:
            req.error(str(e), code=500)
    server.add_endpoint('GET', '/weight', handle_weight)
    
    def handle_barometer(req):
        try:
            t,p = sensors.read_temp_pressure()
            req.reply(ext_temperature=t, ext_pressure=p)
        except Exception as e:
            req.error(str(e), code=500)
    server.add_endpoint('GET', '/barometer', handle_barometer)
    
    def handle_temp_humid(req):
        try:
            params = {}
            for i,(temp,humid) in enumerate(sensors.read_all_temp_humid()):
                params[f'temperature_{i}'] = temp
                params[f'humidity_{i}'] = humid
            req.reply(**params)
        except Exception as e:
            req.error(str(e), code=500)
    server.add_endpoint('GET', f'/temp_humid', handle_temp_humid)
    
    def generate_handler(idx):
        def _handler(req):
            try:
                t,h = sensors.read_temp_humid(idx)
                params = {
                    f'temperature_{idx}': t,
                    f'humidity_{idx}': h
                }
                req.reply(**params)
            except Exception as e:
                req.error(str(e), code=500)
        return _handler            
    
    for idx in range(TOTAL_AHT10):
        server.add_endpoint('GET', f'/temp_humid/{idx}', generate_handler(idx))

    def handle_init_log(req):
        try:
            req.reply(init_log=sensors.init_issues)
        except Exception as e:
            req.error(str(e), code=500)
    server.add_endpoint('GET', '/init_log', handle_init_log)
    
    def handle_reset(req):
        req.reply(msg='resetting')
        machine.reset()
    server.add_endpoint('POST', '/reset', handle_reset)

    def handle_repl(req):
        req.reply(msg='dropping to repl')
        raise Exception('dropping to repl')
    server.add_endpoint('POST', '/repl', handle_repl)

    print('Waiting for requests...')
    server.serve()

except Exception as e:
    print(e)
    raise
