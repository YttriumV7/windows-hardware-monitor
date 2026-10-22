"""
    Some of this script is from https://thepythoncode.com/article/get-hardware-system-information-python which i used to test how python can return 
    system information.
"""


import platform
import sys
import time
from datetime import datetime
import os
import subprocess

import psutil

def bytes_to_human(value, suffix="B"):
    if value is None:
        return "N/A"
    value = float(value)
    for unit in ("", "K", "M", "G", "T", "P"):
        if abs(value) < 1024:
            return f"{value:.2f}{unit}{suffix}"
        value /= 1024
    return f"{value:.2f}EB"


def seconds_to_human(seconds):
    if seconds is None or seconds < 0:
        return "N/A"
    seconds = int(seconds)
    days, remainder = divmod(seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)


def timestamp_to_iso(timestamp):
    return datetime.fromtimestamp(timestamp).astimezone().isoformat(timespec="seconds")


uname = platform.uname()
boot_time = psutil.boot_time()

print("System:", uname.system)
print("Node:", uname.node)
print("Release:", uname.release)
print("Machine:", uname.machine)
print("Architecture:", platform.architecture()[0])
print("Python:", platform.python_version())
print("Python executable:", sys.executable)
print("Boot time:", timestamp_to_iso(boot_time))
print("Uptime:", seconds_to_human(time.time() - boot_time))

freq = psutil.cpu_freq()
print("Physical cores:", psutil.cpu_count(logical=False))
print("Logical cores:", psutil.cpu_count(logical=True))

if freq:
    print("Current frequency:", round(freq.current, 2), "MHz")
    print("Min frequency:", round(freq.min, 2), "MHz")
    print("Max frequency:", round(freq.max, 2), "MHz")

per_core = psutil.cpu_percent(interval=0.5, percpu=True)
print("Per-core usage:", per_core)
print("Total CPU usage:", psutil.cpu_percent(interval=None), "%")

if hasattr(os, "getloadavg"):
    print("Load average:", os.getloadavg())

svmem = psutil.virtual_memory()
swap = psutil.swap_memory()

print("Total RAM:", bytes_to_human(svmem.total))
print("Available RAM:", bytes_to_human(svmem.available))
print("Used RAM:", bytes_to_human(svmem.used))
print("RAM usage:", svmem.percent, "%")

print("Total swap:", bytes_to_human(swap.total))
print("Used swap:", bytes_to_human(swap.used))
print("Swap usage:", swap.percent, "%")




print("Processor:", platform.processor())


#returns the name of the cpu
def get_cpu_name():
    return subprocess.check_output(
        ["powershell", "-Command", "(Get-CimInstance Win32_Processor).Name"],
        text=True
    ).strip()

cpu_name = get_cpu_name()

#print(cpu_name)






#self.{label} = ctk.CTkLabel(
    #self.cpu_details_frame,
    #text="CPU: Loading...",
    #font=ctk.CTkFont(size=16)
#)

#self.{label}.grid(
    #row=0,
    #column=0,
    #sticky="w",
    #padx=20,
    #pady=10
#)

cpu_info = psutil.cpu_freq()

print("Current frequency:", round(cpu_info.current, 2), "MHz")




import winreg

key = winreg.OpenKey(
    winreg.HKEY_LOCAL_MACHINE,
    r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
)

cpu_namesecond = winreg.QueryValueEx(key, "ProcessorNameString")[0]

print(cpu_namesecond)