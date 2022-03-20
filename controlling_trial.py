import datetime
# import RPi.GPIO as GPIO
GPIO = ''
import time
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from config import *


def switch_on():
    GPIO.output(relayPIN, GPIO.HIGH)
    servo.ChangeDutyCycle(6)
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)


def switch_off():
    GPIO.output(relayPIN, GPIO.HIGH)
    time.sleep(0.5)
    servo.ChangeDutyCycle(2.5)
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)


def fuzzy_check(pitch_in, roll_in):
    #  Set Semesta
    pitch = ctrl.Antecedent(np.arange(0, 51, 1), 'pitch')
    roll = ctrl.Antecedent(np.arange(0, 51, 1), 'roll')
    switch = ctrl.Consequent(np.arange(0, 100, 1), 'switch')

    # Derajat Keanggotaan (3, 5, 7)
    pitch.automf(3)
    roll.automf(3)

    # Fuzzyfikasi
    switch['low'] = fuzz.trimf(switch.universe, [0, 0, 50])
    switch['medium'] = fuzz.trimf(switch.universe, [0, 50, 100])
    switch['high'] = fuzz.trimf(switch.universe, [50, 100, 100])

    # Set Rule
    rule1 = ctrl.Rule(pitch['poor'] | roll['poor'], switch['low'])
    rule2 = ctrl.Rule(pitch['average'], switch['medium'])
    rule3 = ctrl.Rule(roll['average'], switch['medium'])
    rule4 = ctrl.Rule(roll['good'] | pitch['good'], switch['high'])

    # Control System Berdasarkan Rule
    switching_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4])
    switching = ctrl.ControlSystemSimulation(switching_ctrl)

    # Set Input Dari Sensor
    switching.input['pitch'] = pitch_in
    switching.input['roll'] = roll_in
    switching.compute()
    return switching.output['switch']


def wave():
    db.execute("SELECT ABS(pitch), ABS(roll) FROM `s_accelo` ORDER BY id DESC LIMIT 1")
    pitch, roll = db.fetchone()
    print("\nPitch IN :", pitch)
    print("Roll IN : ", roll)
    value = fuzzy_check(pitch, roll)
    print("Value :", value)

    if value < 50:
        status_wave = "low"
    else:
        status_wave = "high"

    db.execute("INSERT INTO r_fuzzy(`value`, `status`, created_at, updated_at) VALUES "
               "('%s', '%s', '%s', '%s')" % (value, status, datetime.datetime.now(), datetime.datetime.now()))
    return status_wave


def pakan():
    while True:
        db.execute("SELECT ABS(pitch), ABS(roll) FROM `s_accelo` ORDER BY id DESC LIMIT 1")
        pitch, roll = db.fetchone()
        print(f"\nPitch IN : {pitch}")
        print(f"Roll IN : {roll}")
        value = fuzzy_check(pitch, roll)
        print("Value :", value)

        if value < 50:
            print("Pakan ON")
            status = "low"
            switch_on()
        else:
            print("Pakan OFF")
            status = "high"
            switch_off()

        db.execute("INSERT INTO r_fuzzy(`value`, `status`, created_at, updated_at) VALUES "
                   "('%s', '%s', '%s', '%s')" % (value, status, datetime.datetime.now(), datetime.datetime.now()))
        time.sleep(1)


if __name__ == '__main__':
    servoPIN = 18
    relayPIN = 13

    # GPIO.setmode(GPIO.BCM)
    # GPIO.setup(servoPIN, GPIO.OUT)
    # GPIO.setup(relayPIN, GPIO.OUT)
    # GPIO.setwarnings(False)
    #
    # servo = GPIO.PWM(servoPIN, 50)  # GPIO 17 for PWM with 50Hz
    # servo.start(2.5)  # Initialization

    try:
        while True:
            timestamp = datetime.datetime.now()
            hour = timestamp.strftime('%H')
            hour = hour[1] if hour[0] == '0' else hour

            # Cek Pakan
            db.execute("SELECT durasi, HOUR(TIME), `status` FROM `c_jadwal`")
            pakan_dict = {}
            for durasi, jam, status in db.fetchall():
                print(durasi, jam, status)
                pakan_dict[status] = jam
                if status == 'waiting' and str(jam) == hour:
                    pakan()


            exit()
    except KeyboardInterrupt:
        servo.stop()
        GPIO.cleanup()
