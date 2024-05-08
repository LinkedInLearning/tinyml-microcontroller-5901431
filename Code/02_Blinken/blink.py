from machine import Pin  # type: ignore
from time import sleep

led = Pin(25, Pin.OUT)

while True:
    led.on()
    sleep(0.5)
    led.off()
    sleep(0.5)

