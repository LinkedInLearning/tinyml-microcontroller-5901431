import os
from machine import Pin
from time import sleep

def list_files():
    files = os.listdir()
    if (len(files) == 0):
        print("No files found")
    for file in files:
        print(file)

Pin(25, Pin.OUT).on()
list_files()
# sleep(1)
Pin(25, Pin.OUT).off()

