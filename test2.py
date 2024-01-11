import threading
import busio
import RPi.GPIO as GPIO
import board
from adafruit_pn532.i2c import PN532_I2C
from time import sleep, time, localtime, asctime
from tabulate import tabulate
import copy
from flask import Flask, render_template
from pcf8575 import PCF8575
import neopixel




#pcf8575 setup
pcf_address = 0x20
i2c_port_num = 1
pcf = PCF8575(i2c_port_num, pcf_address)


app = Flask(__name__)
#log file setup + boot time
file = open("log.txt", "a")
file.write("Booted at: " + asctime(localtime()))
file.close()

i2c = busio.I2C(board.SCL, board.SDA)
GPIO.setmode(GPIO.BCM)
#leds setup
R_led = 27
G_led = 22

GPIO.setup(R_led, GPIO.OUT)
GPIO.setup(G_led, GPIO.OUT)

uidSave = None
cardTime = time()
logoutTime = 10
head = ["pin", "status", "uid", "time"]

#set all available docks
DATA = [[0, False, "", "",[]], [1, False, "", ""]]
#copy of the data to check if the status of the boxes changed
oldDATA = copy.deepcopy(DATA)

#neopixel setup
pixels = neopixel.NeoPixel(board.D18, len(DATA), brightness=0.2)

#setup of the pn532
pn532 = PN532_I2C(i2c, debug=False)
ic, ver, rev, support = pn532.firmware_version
pn532.SAM_configuration()

def run_flask():
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=80)

def box_colors():
    for i in range(len(DATA)):
        if DATA[i][1] == True:
            pixels[i] = (0, 255, 0)
        elif DATA[i][2] == "STOLEN":
            pixels[i] = (255, 0, 0)
        else: 
            pixels[i] = (0, 0, 255)

def return_box():


def check_boxes():
    for i in range(len(DATA)):
        box_pin = DATA[i][0]
        DATA[i][1] = pcf.port[box_pin]  == True

def check_card():
    global uidSave, cardTime
    uid = pn532.read_passive_target(timeout=0.5)
    if uid is None:
        if time() - cardTime > logoutTime:
            uidSave = None
            GPIO.output(G_led, False)
        return uidSave
     
    print("Found card with UID:", [hex(i) for i in uid])
    cardTime = time() 
    uidSave = uid
    GPIO.output(G_led, True)
    return uid

def check_change(uid):
    for i in range(len(DATA)):
        if oldDATA[i][1] != DATA[i][1]:
            if DATA[i][1] == False:
                print(f"Box {i + 1} changed")
                if uid is None:
                    print("Insert Card")
                    timeBefore = time()
                    while True:
                        print(". ")
                        GPIO.output(R_led, True)
                        uid = check_card()
                        if uid is not None:
                                GPIO.output(R_led, False)
                                break
                        if time() - timeBefore > 10:
                            print("STOLEN")
                            log(f"Box {i + 1} stolen at {asctime(localtime())}")
                            DATA[i][2] = "STOLEN"
                            DATA[i][3] = asctime(localtime())
                            oldDATA[i][1] = DATA[i][1]
                            return
                DATA[i][2] = ''.join([format(byte, '02x') for byte in uid])
                DATA[i][3] = asctime(localtime())
                GPIO.output(R_led, False)
                log(f"Box {i + 1} borrowed by: {DATA[i][2]} at {DATA[i][3]}")
                oldDATA[i][1] = DATA[i][1]
            else:
                DATA[i][2] = "RETURNED by:"+ DATA[i][2]
                print(f"Box {i + 1} returned")
                oldDATA[i][1] = DATA[i][1]
                log(f"Box {i + 1} returned by: {DATA[i][2]} at {DATA[i][3]}")
                DATA[i][3] = asctime(localtime())

def log(data):
    file = open("log.txt", "a")
    file.write(data+"\n")
    file.close()

def main():
    while True:
        sleep(1)
        check_boxes()
        box_colors()
        uidSave = check_card()
        check_change(uidSave)
        table_data = copy.deepcopy(DATA)
        print(tabulate(table_data, headers=head))
        print("")

#The main thread is used to check the boxes and the card
main_thread = threading.Thread(target=main)
#The flask thread is used to run the flask server
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
main_thread.start()

@app.route('/')
def index():
    table_data = copy.deepcopy(DATA)
    uidR= uidSave
    return render_template('index.html', table_data=table_data, headers=head, uid=uidR)


if __name__ == '__main__':
    while True:
        sleep(1)
        
