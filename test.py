import busio
import RPi.GPIO as GPIO
import board
from adafruit_pn532.i2c import PN532_I2C
from time import sleep
import copy
from tabulate import tabulate

i2c = busio.I2C(board.SCL, board.SDA)

DATA = [[4, 0, ""], [17, 0, ""]]
# [pin, status]
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

pn532 = PN532_I2C(i2c, debug=False)

ic, ver, rev, support = pn532.firmware_version
print("Found PN532 with firmware version: {0}.{1}".format(ver, rev))

pn532.SAM_configuration()

oldDATA = copy.deepcopy(DATA)  # Initialize oldDATA

def check_boxes():
    i = 0
    while i < len(DATA):
        box_pin = DATA[i][0]
        if GPIO.input(box_pin) == GPIO.HIGH:
            #print(f"Box {i + 1} is there")
            DATA[i][1] = 1
        else:
            #print(f"Box {i + 1} is not there")
            DATA[i][1] = 0
        i += 1

def check_card():
    global uidSave
    # Check if a card is available to read
    uid = pn532.read_passive_target(timeout=0.5)
    # Try again if no card is available.
    if uid is None:
        return uidSave
    print("Found card with UID:", [hex(i) for i in uid])
    uidSave = uid
    return uid


def check_change(uid):
    for i in range(len(DATA)):
        if oldDATA[i][1] != DATA[i][1]:
            print(f"Box {i + 1} changed")
            DATA[i][2] = ''.join([format(byte, '02x') for byte in uid])
            oldDATA[i][1] = DATA[i][1]


while True:
    check_boxes()
    uidSave = check_card()
    if uidSave is not None:
        check_change(uidSave)
    print(tabulate(DATA, tablefmt="grid"))
    sleep(1)
