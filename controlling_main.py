import datetime
import sys
import time
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from config import *


def hour_now():
    timestamp = datetime.datetime.now()
    hour = timestamp.strftime('%H')
    return hour[1] if hour[0] == '0' else hour


def insert_sensor(table, value, value2, status):
    date = datetime.datetime.now()
    if not value2:
        con.execute(f"INSERT INTO `{table}` (`value`, `status`, created_at, updated_at) "
                   f"VALUES('{value}', '{status}', '{date}', '{date}')")
    else:
        con.execute(f"INSERT INTO `{table}` VALUES('{value}', '{value2}', '{date}', '{date}')")


def set_relay(relay, flag):
    con.execute(f"UPDATE c_relay SET flag = '{flag}', updated_at = '{date_now}' "
                f"WHERE relay = '{relay}'")


def fuzzy_check():
    con.execute("SELECT ABS(pitch), ABS(roll) FROM `s_accelo` ORDER BY id DESC LIMIT 1")
    pitch_in, roll_in = con.fetchone()
    print("\nPitch IN :", pitch_in, "Roll IN : ", roll_in)

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
    value = switching.output['switch']

    if value < 50:
        status_wave = "low"
    else:
        status_wave = "high"
    con.execute(f"INSERT INTO r_fuzzy(`value`, `status`, created_at, updated_at) VALUES "
                f"('{value}', '{status}', '{datetime.datetime.now()}', '{datetime.datetime.now()}')")
    return value, status_wave


def pakan():
    print("Start Feeding")
    set_relay('Auto Feeding', 1)
    time.sleep(5)
    value_temp, status_wave = fuzzy_check()
    while True:
        value_fuzzy, status_wave = fuzzy_check()
        if value_temp < value_fuzzy:
            value_temp = value_fuzzy
        elif value_temp > value_fuzzy:
            print("Stop Feeding")
            set_relay('Auto Feeding', 0)
            break
        else:
            print("Auto Feeding Looping Error - Force Stop")
            set_relay('Auto Feeding', 0)
            break
        time.sleep(5)


def sirkulasi():
    print("Open Valve")
    set_relay('Auto Valve', 1)
    time.sleep(60 * 10)

    print("Start Pump")
    set_relay('Water Pump', 1)
    time.sleep(60 * 5)

    print("Close Valve")
    set_relay('Auto Valve', 0)

    time.sleep(60 * 30)
    print("Off Pump")
    set_relay('Auto Valve', 0)


if __name__ == '__main__':
    while True:
        con = db()
        # Cek Pakan
        date_now = datetime.datetime.now()
        print("cek controling ", date_now)
        con.execute("SELECT `interval`, HOUR(TIME), `status` FROM `c_jadwal`")
        pakan_dict = {}
        for interval, jam, status in con.fetchall():
            # print(durasi, jam, status)
            pakan_dict[status] = jam, interval
        for status in pakan_dict:
            jam, interval = pakan_dict[status]
            if status == 'next run' and str(jam) == hour_now():
                # update dari next run ke runing
                con.execute(f"UPDATE c_jadwal SET `status` = 'runing', updated_at = '{date_now}' "
                           f"WHERE `status` = 'next run'")
                pakan(interval)
                # update dari waiting ke next run
                con.execute(f"UPDATE c_jadwal SET `status` = 'next run', updated_at = '{date_now}' "
                           f"WHERE `status` = 'waiting'")
                # update dari last run ke waiting
                con.execute(f"UPDATE c_jadwal SET `status` = 'waiting', updated_at = '{date_now}' "
                           f"WHERE `status` = 'last run'")
                # update dari running ke last run
                con.execute(f"UPDATE c_jadwal SET `status` = 'last run', updated_at = '{date_now}' "
                           f"WHERE `status` = 'running'")
        # for status in pakan_dict:
        #     jam, durasi = pakan_dict[status]
            elif status != 'next run' and str(jam) != hour_now():
                # Cek Kekeruhan
                con.execute("SELECT `status` FROM `s_turbidity` WHERE id = (SELECT MAX(id) FROM `s_turbidity`);")
                status_turbidity = con.fetchone()[0]
                con.execute("SELECT `status` FROM `s_ph` WHERE id = (SELECT MAX(id) FROM `s_ph`);")
                status_ph = con.fetchone()[0]
                if status_turbidity == 'keruh' or status_ph == "asam":
                    print("start sirkulasi air")
                    sirkulasi()
            else:
                print("No Action Needed")
        t = 360
        while t:
            mins, secs = divmod(t, 60)
            sys.stdout.write(f"\rWaiting for next action {mins:02d}:{secs:02d}")
            sys.stdout.flush()
            time.sleep(1)
            t -= 1
        print("")
