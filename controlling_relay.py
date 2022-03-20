import datetime
import time
import RPi.GPIO as GPIO
import requests

from config import db


def gpio_on(pin_gpio):
    GPIO.setup(pin_gpio, GPIO.OUT)
    GPIO.output(pin_gpio, GPIO.LOW)


def gpio_off(pin_gpio):
    GPIO.setup(pin_gpio, GPIO.OUT)
    GPIO.output(pin_gpio, GPIO.HIGH)


if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT)
    GPIO.setup(12, GPIO.OUT)
    servo = GPIO.PWM(18, 50)  # GPIO 18 for PWM with 50Hz
    # motor = GPIO.PWM(12, 50)  # GPIO 12 for PWM with 50Hz
    servo.start(2.5)  # Initialization
    # motor.start(0)
    valve_temp = 0
    gpio_off(4)
    gpio_off(17)
    gpio_off(27)
    gpio_off(22)
    while True:
        
        try:
            print(datetime.datetime.now())
            data = requests.get("https://kayonkreatif.com/yoga/api_raspi/api/controlling_relay").json()
            # print(data)
            if data['code'] == 200:
                for row in data['data']:
                    id_relay, pin, relay, flag, created_at, updated_at = row.values()
                    pin = int(pin)
                    # print(id_relay, pin, relay, flag, created_at, updated_at)
                    if flag == '1':
                        if relay == 'Auto Feeding':
                            # motor.ChangeDutyCycle(100)
                            gpio_on(pin)
                            time.sleep(1)
                            servo.ChangeDutyCycle(6)
                            time.sleep(1)
                            servo.ChangeDutyCycle(0)
                        elif relay == 'Auto Valve':
                            if valve_temp == 0:
                                print("OPENING VALVE")
                                gpio_on(4)
                                gpio_on(17)
                                time.sleep(25)
                                print("HOLDING POSITION")
                                gpio_off(4)
                                gpio_off(17)
                                valve_temp = 1
                        else:
                            gpio_on(pin)
                        print(relay, 'is ON')
                    elif flag == '0':
                        if relay == 'Auto Feeding':
                            # motor.ChangeDutyCycle(0)
                            servo.ChangeDutyCycle(2.5)
                            time.sleep(0.5)
                            servo.ChangeDutyCycle(0)
                            time.sleep(1)
                            gpio_off(pin)
                        elif relay == 'Auto Valve':
                            if valve_temp == 1:
                                print("CLOSING VALVE")
                                gpio_on(27)
                                gpio_on(22)
                                time.sleep(25.5)
                                print("HOLDING POSITION")
                                gpio_off(27)
                                gpio_off(22)
                                valve_temp = 0
                        else:
                            gpio_off(pin)
                        print(relay, 'is off')
                    else:
                        print("Error Relay Condition")
                print('\n')
                time.sleep(1)
            else:
                print("Failed get Data !")
        except Exception as e:
            print(e)
            print("Connection Refuse by Server")
