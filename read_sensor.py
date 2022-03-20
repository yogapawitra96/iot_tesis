import datetime
import time
import serial
from config import *


def insert_sensor(table, value, value2, status):
    date = datetime.datetime.now()
    if not value2:
        con.execute("INSERT INTO %s (`value`, `status`, created_at, updated_at) VALUES('%s', '%s', '%s', '%s')" % (table, value, status, date, date))
    else:
        con.execute("INSERT INTO %s (`pitch`, `roll`, created_at, updated_at) VALUES('%s', '%s', '%s', '%s')" % (table, value, value2, date, date))


if __name__ == '__main__':
    while True:
        try:
            date_now = datetime.datetime.now()
            con = db()
            print(date_now)
            read_serial = serial.Serial('/dev/ttyACM0', 9600).readline()
            read_serial = str(read_serial).replace("b'", "").replace("\\", "").replace("rn'", "").split()
            data = read_serial[0].split(";")
            #print(data)

            pitch = float(data[1])
            roll = float(data[3])

            turbidity = float(data[5]) + 0.2
            if turbidity < 2.5:
                ntu = 3000
            else:
                ntu = -1120.4*(turbidity*turbidity)+5742.3*turbidity-4353.8
            print(f"turbidity : {ntu} ntu, volt : {turbidity} v")
            if ntu < 20:
                turbidity_status = "keruh"
            elif ntu > 70:
                turbidity_status = "bersih"
            else:
                turbidity_status = "sedang"

            ph = float(data[7]) + 2
            if ph < 7:
                ph_status = "asam"
            elif ph > 7:
                ph_status = "basa"
            else:
                ph_status = "normal"

            ultrasonic_1 = float(data[9])
            sensor_ke_air = ultrasonic_1 + 4
            tinggi_kolam = 100
            sensor_ke_kolam = 20
            tinggi_air = (tinggi_kolam + sensor_ke_kolam) - sensor_ke_air
            persentase_air = round(tinggi_air / tinggi_kolam * 100)
            if persentase_air < 60:
                water_level_status = "tinggi"
            elif persentase_air > 40:
                water_level_status = "normal"
            else:
                water_level_status = "rendah"
            print(f"Tinggi Air : {tinggi_air}cm, Persentase tinggi air : {persentase_air}%")

            ultrasonic_2 = float(data[11])
            sensor_ke_pakan = ultrasonic_2
            sensor_ke_dasar_galon = 30
            tinggi_pakan = sensor_ke_dasar_galon - sensor_ke_pakan
            persentase_pakan = round(tinggi_pakan / sensor_ke_dasar_galon * 100)
            if persentase_pakan < 20:
                pakan_status = "penuh"
            elif persentase_pakan > 70:
                pakan_status = "sedang"
            else:
                pakan_status = "sedikit"
            print(f"Tinggi Pakan : {tinggi_pakan}cm, Persentase pakan : {persentase_pakan}%")

            print("pitch:", pitch, "roll:", roll, "turbidity:", turbidity, "ph:", ph, "ultrasonic_1:", ultrasonic_1, "ultrasonic_2", ultrasonic_2)

            con.execute("SELECT flag FROM c_relay WHERE relay='Auto Feeding'")
            flag_relay = con.fetchone()[0]
            con.execute("SELECT DATE_ADD(created_at, INTERVAL 1 HOUR) FROM `s_accelo` ORDER BY id DESC LIMIT 1;")
            date_next = con.fetchone()[0]
            if flag_relay == '1' or date_next <= datetime.datetime.now():
                print("inserting data...")
                insert_sensor("s_accelo", pitch, roll, False)
                insert_sensor("s_turbidity", ntu, False, turbidity_status)
                insert_sensor("s_ph", ph, False, ph_status)
                insert_sensor("s_pakan", persentase_pakan, False, pakan_status)
                insert_sensor("s_water_level", persentase_air, False, water_level_status)
            print("##########-ALL DONE-##########\n")

        except Exception as e:
            print(e)
        time.sleep(0.5)

