import datetime
import time
import serial
from config import *


def insert_sensor(table, value, value2, status):
    date = datetime.datetime.now()
    if status is True:
        con.execute("INSERT INTO %s (`pitch`, `roll`, created_at, updated_at) VALUES('%s', '%s', '%s', '%s')" % (table, value, value2, date, date))
    else:
        con.execute("INSERT INTO %s (`value`, `status`, created_at, updated_at) VALUES('%s', '%s', '%s', '%s')" % (table, value, status, date, date))


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

            pitch = abs(float(data[1]))
            roll = abs(float(data[3]))

            turbidity = float(data[5]) + 0.38
            if turbidity < 2.5:
                ntu = 3000
            else:
                ntu = -1120.4*pow(turbidity, 2)+5742.3*turbidity-4352.9
            if ntu > 2000:
                turbidity_status = "keruh"
            elif ntu > 1000:
                turbidity_status = "sedang"
            else:
                turbidity_status = "bersih"
            print(f"turbidity : {ntu} ntu, volt : {turbidity} v, status : {turbidity_status}")

            ph = float(data[7]) + 2
            if ph < 7:
                ph_status = "asam"
            elif ph > 8:
                ph_status = "basa"
            else:
                ph_status = "normal"
            print(f"ph : {ph}, status : {ph_status}")

            ultrasonic_1 = float(data[9])
            sensor_ke_air = ultrasonic_1 + 4
            tinggi_kolam = 100
            sensor_ke_kolam = 20
            tinggi_air = (tinggi_kolam + sensor_ke_kolam) - sensor_ke_air
            persentase_air = round(tinggi_air / tinggi_kolam * 100)
            if persentase_air <= 20:
                water_level_status = "rendah"
            elif persentase_air <= 50:
                water_level_status = "sedang"
            else:
                water_level_status = "tinggi"
            print(f"Tinggi Air : {tinggi_air}cm, Persentase tinggi air : {persentase_air}%, status : {water_level_status}")

            ultrasonic_2 = float(data[11])
            sensor_ke_pakan = ultrasonic_2
            sensor_ke_dasar_galon = 30
            tinggi_pakan = sensor_ke_dasar_galon - sensor_ke_pakan
            persentase_pakan = round(tinggi_pakan / sensor_ke_dasar_galon * 100)
            if persentase_pakan <= 20:
                pakan_status = "sedikit"
            elif persentase_pakan <= 50:
                pakan_status = "sedang"
            else:
                pakan_status = "penuh"
            print(f"Tinggi Pakan : {tinggi_pakan}cm, Persentase pakan : {persentase_pakan}%, status : {pakan_status}")

            print("pitch:", pitch, "roll:", roll, "turbidity:", turbidity, "ph:", ph, "ultrasonic_1:", ultrasonic_1, "ultrasonic_2", ultrasonic_2)

            con.execute("SELECT flag FROM c_relay WHERE relay='Auto Feeding'")
            flag_relay = con.fetchone()[0]
            con.execute("SELECT DATE_ADD(created_at, INTERVAL 1 HOUR) FROM `s_accelo` ORDER BY id DESC LIMIT 1;")
            date_next = con.fetchone()[0]
            if flag_relay == '1' or date_next <= datetime.datetime.now():
                print("inserting data...")
                insert_sensor("s_accelo", pitch, roll, True)
                insert_sensor("s_turbidity", ntu, False, turbidity_status)
                insert_sensor("s_ph", ph, False, ph_status)
                insert_sensor("s_pakan", persentase_pakan, False, pakan_status)
                insert_sensor("s_water_level", persentase_air, False, water_level_status)
            print("##########-ALL DONE-##########\n")

        except Exception as e:
            print(e)
        time.sleep(0.5)

