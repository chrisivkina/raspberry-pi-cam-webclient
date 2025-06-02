import subprocess
from config import config
from time import time

# the amount of time in seconds to wait before updating the data
sys_data_intervals = {
    'cpu_temp': 2,
    'gpu_temp': 2,
    'battery_low': 2,
    'uptime': 45,
    'disk_space': 60
}


class DataCache:
    def __init__(self):
        self.cpu_temp = None
        self.gpu_temp = None
        self.battery_low = None
        self.uptime = None
        self.disk_space = None

        self.cpu_temp_set_time = 0
        self.gpu_temp_set_time = 0
        self.battery_low_set_time = 0
        self.uptime_set_time = 0
        self.disk_space_set_time = 0

    def cpu_temp_is_stale(self):
        return self.cpu_temp_set_time is None or time() - self.cpu_temp_set_time > sys_data_intervals['cpu_temp']
    
    def set_cpu_temp(self, value):
        self.cpu_temp = value
        self.cpu_temp_set_time = time()

    def gpu_temp_is_stale(self):
        return self.gpu_temp_set_time is None or time() - self.gpu_temp_set_time > sys_data_intervals['gpu_temp']
    
    def set_gpu_temp(self, value):
        self.gpu_temp = value
        self.gpu_temp_set_time = time()

    def battery_low_is_stale(self):
        return self.battery_low_set_time is None or time() - self.battery_low_set_time > sys_data_intervals['battery_low']
    
    def set_battery_low(self, value):
        self.battery_low = value
        self.battery_low_set_time = time()

    def uptime_is_stale(self):
        return self.uptime_set_time is None or time() - self.uptime_set_time > sys_data_intervals['uptime']
    
    def set_uptime(self, value):
        self.uptime = value
        self.uptime_set_time = time()

    def disk_space_is_stale(self):
        return self.disk_space_set_time is None or time() - self.disk_space_set_time > sys_data_intervals['disk_space']
    
    def set_disk_space(self, value):
        self.disk_space = value
        self.disk_space_set_time = time()

    def get_cpu_temp(self):
        return self.cpu_temp
    
    def get_gpu_temp(self):
        return self.gpu_temp
    
    def get_battery_low(self):
        return self.battery_low
    
    def get_uptime(self):
        return self.uptime
    
    def get_disk_space(self):
        return self.disk_space
        

data_cache = DataCache()


class Pi:
    @property
    def cpu_temp(self):
        if data_cache.cpu_temp_is_stale():
            if config['CONFIG_LOCAL_MODE']:
                return "55.3°C"

            temp = subprocess.check_output("cat /sys/class/thermal/thermal_zone0/temp", shell=True).decode("utf-8")
            temp = f"{float(temp) / 1000}°C"
            data_cache.set_cpu_temp(temp)
            return temp
        else:
            return data_cache.get_cpu_temp()

    @property
    def gpu_temp(self):
        if data_cache.gpu_temp_is_stale():
            if config['CONFIG_LOCAL_MODE']:
                return "48.7°C"

            temp = subprocess.check_output("vcgencmd measure_temp", shell=True).decode("utf-8")
            temp = temp.replace("temp=", "").replace("'C\n", "°C")
            data_cache.set_gpu_temp(temp)
            return temp
        else:
            return data_cache.get_gpu_temp()

    @property
    def battery_low(self):
        if data_cache.battery_low_is_stale():
            if config['CONFIG_LOCAL_MODE']:
                return "0x0"

            batt = subprocess.check_output("vcgencmd get_throttled", shell=True).decode("utf-8")
            batt = batt.replace("throttled=", "").strip()

            # So you got
            # 101 0000 0000 0000 0101

            # That, counting from the right and starting at 0 says that bits 0, 2, 16 and 18 are set.

            # 0 means "Under-voltage currently detected"
            # 2 means "Currently throttled"
            # 16 means "Under-voltage has occurred"
            # 18 means "Throttling has occurred"

            # So if you have 0x50005, you have all of those things.
            # If you have 0x0, you have none of those things.

            # convert hex string to int
            batt = int(batt, 16)

            # extract bit 0
            under_volt_detected = batt & 1

            # extract bit 2
            throttled = (batt >> 2) & 1

            string = f'Undervolted: {under_volt_detected} | Throttled: {throttled}'
            # example:
            # UndrV/0 Throtl/1
            data_cache.set_battery_low(string)

            return string
        else:
            return data_cache.get_battery_low()

    @property
    def uptime(self):
        if data_cache.uptime_is_stale():
            if config['CONFIG_LOCAL_MODE']:
                return "up 1 day, 1 hour, 1 minute"

            uptime = subprocess.check_output("uptime -p", shell=True).decode("utf-8")

            # returns something like: "up 1 day, 1 hour, 1 minute"

            # replace "up " with "", and replace ", " with ",", day with d, hour with h, minute with m, and remove the s and spaces
            uptime = uptime.replace("up ", "").replace(", ", ",").replace("day", "d").replace("hour", "h").replace("minute", "m").replace('s', '').replace(' ', '')

            data_cache.set_uptime(uptime)
            return uptime
        else:
            return data_cache.get_uptime()

    @property
    def disk_space(self):
        if data_cache.disk_space_is_stale():
            if config['CONFIG_LOCAL_MODE']:
                all_info = "/dev/mmcblk0p2  60553068 6535404  50909312  12% /"
            else:
                all_info = subprocess.check_output("df | grep \"/dev/mmcblk0p2\"", shell=True).decode("utf-8")

            all_info = ' '.join(all_info.split())

            # outputs:
            # Filesystem      Size     Used     Avail     Use% Mounted on
            # /dev/mmcblk0p2  60553068 6535404  50909312  12%  /

            all_info = all_info.split(" ")
            absolute_free = f"{int(all_info[3].strip()) // 1024} MB",
            percentage_used = all_info[4]

            data_cache.set_disk_space([absolute_free, percentage_used])

            return [absolute_free, percentage_used]
        else:
            return data_cache.get_disk_space()


def get_wifi_connection_status():
    return subprocess.check_output("iwconfig 2>&1 | grep ESSID", shell=True).decode("utf-8")
