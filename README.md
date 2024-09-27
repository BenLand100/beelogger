# BeeLogger
## Version 1

This is Micro Python firmware for an Olimex ESP32-PoE board containing some I2C
and SPI sensors intended for monitoring a beehive. A very simple JSON reply 
server with endpoints for different sensor types is embedded for readout.

Supports:
- AHT10 - temperature / humidity
- BMP180 - barometer
- HX711 - ADC intended for strain gauges (weight)
- VEML770 - ambient light sensor

Most of this hardware support code was cobbled together from things found in
the public domain, and various issues were fixed along the way. 

Further documentation to be written at a later date.
