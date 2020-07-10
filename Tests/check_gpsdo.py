import uhd
import datetime as dt

u = uhd.usrp.MultiUSRP()

gpstime = u.get_mboard_sensor("gps_time")
gpstimedt = dt.datetime.fromtimestamp(gpstime.to_real())
print(gpstime)

gpslocked = u.get_mboard_sensor("gps_locked").to_bool()
gprmc = u.get_mboard_sensor("gps_gprmc")
print(gprmc.value)

if gpslocked is False:
    print("GPS not locked")
    exit()

gpgga = u.get_mboard_sensor("gps_gpgga")
print(gpgga.value)
