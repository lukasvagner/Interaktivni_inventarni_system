import threading
import busio
import RPi.GPIO as GPIO
import board
from adafruit_pn532.i2c import PN532_I2C
from time import sleep, time, localtime, asctime
from tabulate import tabulate
import copy
from flask import Flask, render_template, request, redirect, url_for
from pcf8575 import PCF8575
import neopixel
import pickle
#http://192.168.0.192/

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

#buzzer setup
buzzer = 1
GPIO.setup(buzzer, GPIO.OUT)

#leds setup
R_led = 23
G_led = 22

GPIO.setup(R_led, GPIO.OUT)
GPIO.setup(G_led, GPIO.OUT)

uidSave = None #variable that saves the card uid
cardTime = time() 
logoutTime = 4 #time before the card is logged out in seconds
head = ["pin", "status", "uid", "time","Returned correctly","name"] #table headers
sleep(0.5)

# File paths
save_file_path = "save.pkl"
log_file_path = "log.txt"

# Save data using pickle
def save(data):
    try:
        with open(save_file_path, "wb") as save_file:
            pickle.dump(data, save_file)
        print("Data saved successfully.")
    except Exception as e:
        print(f"Error saving data: {e}")

# Load data using pickle or initialize with default values
def load():
    try:
        with open(save_file_path, "rb") as save_file:
            loaded_data = pickle.load(save_file)
        return loaded_data
    except FileNotFoundError:
        print("No save file found. Initializing with default values.")
        initial_data = [
            [0, False, "", "", True, ['0x4', '0x5b', '0xc9', '0x4b', '0x11', '0x1', '0x89'], "1"],
            [1, False, "", "", True, ['0x4', '0xa6', '0x51', '0x4b', '0x11', '0x1', '0x89'], "2"],
            [2, False, "", "", True, [], "3"],
            [3, False, "", "", True, ['0x4', '0x24', '0x4a', '0x4d', '0x11', '0x1', '0x89'], "4"],
            [4, False, "", "", True, ['0x4', '0xe5', '0x70', '0x4c', '0x11', '0x1', '0x89'], "5"],
            [5, False, "", "", True, [], "6"],
            [6, False, "", "", True, [], "7"],
            [7, False, "", "", True, [], "8"],
            [8, False, "", "", True, [], "9"],
            [9, False, "", "", True, [], "10"],
        ]
        save(initial_data)  # Save the initial data to create the file
        return initial_data
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

# Load data at the beginning of the script
loaded_data = load()
if loaded_data is not None:
    DATA = loaded_data
    oldDATA = copy.deepcopy(DATA)
    print("Data loaded successfully.")
else:
    print("Initialization with default values failed. Exiting.")
    exit()

#neopixel setup
pixels = neopixel.NeoPixel(board.D18, len(DATA), brightness=255)
sleep(0.5)

#setup of the pn532 
pn532 = PN532_I2C(i2c, debug=False)
ic, ver, rev, support = pn532.firmware_version
pn532.SAM_configuration()

#setup Flask Web
def run_flask():
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=80)

#Sets colors to all boxes
def box_colors(find=False):
    if find != False:
        pixels[find] = (0, 255, 255)
        sleep(0.5)
        pixels[find] = (0, 0, 0)
        return
    buzzerOn = 0
    for i in range(len(DATA)):
        
        if DATA[i][1] == True:
            if DATA[i][4] == True:
                pixels[i] = (0, 255, 0)
                
            else:    
                pixels[i] = (255, 0, 0)
                buzzerOn = 1
        elif DATA[i][2] == "STOLEN":
            pixels[i] = (255, 0, 255)
            buzzerOn = 1
            

        else: 
            pixels[i] = (0, 0, 5)
    GPIO.output(buzzer, buzzerOn)

#Checks if the box was returned right
def return_box(i):
    return_time = time()
    
    while pcf.port[DATA[i][0]] == False:
        pixels[i] = (255, 255, 0)
        sleep(0.2)
        pixels[i] = (0, 0, 0)
        sleep(0.2)
        if time() - return_time > 4:
            break
    DATA[i][4] = True
    check_change(uidSave, i)

#checking if the boxes are still here 
def check_boxes():
    for i in range(len(DATA)):
        box_pin = DATA[i][0]
        DATA[i][1] = pcf.port[box_pin]  == True

#NFC reader always reads 
def check_card():
    global uidSave, cardTime
    pn532.SAM_configuration() #set again in case the power was out for a second
    uid = pn532.read_passive_target(timeout=0.5)

    # if new card isnt read returns old read until it isnt old than returns None
    if uid is None:
        if time() - cardTime > logoutTime:
            uidSave = None
            GPIO.output(G_led, False)
        return uidSave
    
    #dont save variable sets to True if the chip read was Box id chip 
    dontSave = False
    for i in range(len(DATA)):
        if  [hex(i) for i in uid] == DATA[i][5]:
            print("This card is a box")
            return_box(i)
            dontSave = True
            return None 
    #if its not box chip than return card uid            
    if dontSave == False:
        print("Found card with UID:", [hex(i) for i in uid])
        cardTime = time() 
        uidSave = uid
        GPIO.output(G_led, True)
        return uid

#check changes between old Data and newData than calls functions
def check_change(uid, returned_corectly):
    check_boxes()
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
                        pixels[i] = (255, 255, 0)
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
                DATA[i][4] = False
                GPIO.output(R_led, False)
                log(f"Box {i + 1} borrowed by: {DATA[i][2]} at {DATA[i][3]}")
                oldDATA[i][1] = DATA[i][1]
            elif DATA[i][1] == True and returned_corectly == i:
                    DATA[i][2] = "RETURNED by:"+ DATA[i][2]
                    print(f"Box {i + 1} returned")
                    
                    DATA[i][3] = asctime(localtime())
                    DATA[i][4] = True
                    log(f"Box {i + 1} returned by: {DATA[i][2]} at {DATA[i][3]}")
                    oldDATA[i][1] = DATA[i][1]
            else:
                print(f"Box {i + 1} returned incorrectly")
                oldDATA[i][1] = DATA[i][1]
                DATA[i][3] = asctime(localtime())
                DATA[i][4] = False
                log(f"Box {i + 1} returned incorrectly at {DATA[i][3]}")

#writes data to log text file
def log(data):
    file = open(log_file_path, "a")
    file.write(data + "\n")
    file.close()

#main function that calls almost all functions
def main():
    while True:
        sleep(0.2)# slow down the loop
        box_colors()
        uidSave = check_card()
        check_change(uidSave, None)
        save(DATA)
        table_data = copy.deepcopy(DATA)
        table_data_trimed = [row[:-2] + [row[-1]] for row in DATA]
        print(tabulate(table_data_trimed, headers=head, tablefmt="grid"))
        print("")

# The main thread is used to check the boxes and the card
main_thread = threading.Thread(target=main)
# The flask thread is used to run the flask server
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
main_thread.start()

@app.route('/reset_stolen_status', methods=['POST'])
def reset_stolen_status():
    box_id = int(request.form['box_id'])  # Get box ID from the form data
    DATA[box_id][2] = "Status reseted from web"  # Reset the status of the box to an empty string
    DATA[box_id][4] = True  # Set the "Returned correctly" status to True
    DATA[box_id][3] = asctime(localtime())
    save(DATA)  # Save the updated data
    return redirect(url_for('index'))

@app.route('/update_box_name', methods=['POST'])
def update_box_name():
    box_id = int(request.form['box_id'])  # Get box ID from the form data
    new_name = request.form['new_name']   # Get new name from the form data
    DATA[box_id][6] = new_name            # Update the box name in the data
    save(DATA)                            # Save the updated data
    return redirect(url_for('index'))

@app.route('/find_box', methods=['POST'])
def find_box():
    box_id = int(request.form['box_id'])  # Get box ID from the form data                                     
    box_colors(box_id)                     # Set the colors of the boxes
    return redirect(url_for('index'))

@app.route('/')
def index():
    table_data_trimed = [row[:-2] + [row[-1]] for row in DATA]
    table_data = copy.deepcopy(table_data_trimed)  
    uidR = uidSave
    return render_template('index.html', table_data=table_data, headers=head, uid=uidR)

if __name__ == '__main__':
    while True:
        sleep(1)