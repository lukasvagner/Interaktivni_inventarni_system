import threading
import busio
import RPi.GPIO as GPIO
import board
from adafruit_pn532.i2c import PN532_I2C
from time import sleep, time, localtime, asctime
from tabulate import tabulate
import copy
from flask import Flask, render_template

app = Flask(__name__)

file = open("log.txt", "a")
file.write("Booted at: " + asctime(localtime()))
file.close()

i2c = busio.I2C(board.SCL, board.SDA)
led = 27
GPIO.setup(led, GPIO.OUT)

uidSave = None
cardTime = time()
logoutTime = 10
head = ["pin", "status", "uid", "time"]
DATA = [[4, False, "", ""], [17, False, "", ""]]
oldDATA = copy.deepcopy(DATA)

GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

pn532 = PN532_I2C(i2c, debug=False)
ic, ver, rev, support = pn532.firmware_version
pn532.SAM_configuration()

def run_flask():
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=80)



def check_boxes():
    for i in range(len(DATA)):
        box_pin = DATA[i][0]
        DATA[i][1] = GPIO.input(box_pin) == GPIO.HIGH

def check_card():
    global uidSave, cardTime
    uid = pn532.read_passive_target(timeout=0.5)
    if uid is None:
        if time() - cardTime > logoutTime:
            uidSave = None
        return uidSave
     
    print("Found card with UID:", [hex(i) for i in uid])
    cardTime = time() 
    uidSave = uid
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
                        GPIO.output(led, True)
                        uid = check_card()
                        if uid is not None:
                                GPIO.output(led, False)
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
        uidSave = check_card()
        check_change(uidSave)
        table_data = copy.deepcopy(DATA)
        print(tabulate(table_data, headers=head))
        print("")

main_thread = threading.Thread(target=main)
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
main_thread.start()

@app.route('/')
def index():
    table_data = copy.deepcopy(DATA)
    return render_template('index.html', table_data=table_data, headers=head)


if __name__ == '__main__':
    while True:
        sleep(1)
        # Additional processing can be added here in the main thread
