import time
import psutil 
import os

runtime = 0

def display_usage(runtime, cpu_usage, mem_usage, bars=50):
    os.system("cls" if os.name == "nt" else "clear") #clears the terminal before outputting the next set of bars for cleaner display, cls for windows, clear for linux and mac
    cpu_percent = (cpu_usage / 100.0)
    cpu_bar = "█" * int(cpu_percent * bars) + "-" * (bars - int(cpu_percent * bars)) #converts the percentage into a bar
 
    mem_percent = (mem_usage / 100.0) # converts the detected usage to a percentage to make the bar
    mem_bar = "█" * int(mem_percent * bars) + "-" * (bars - int(mem_percent * bars))

    print(f"Runtime: {runtime} seconds") #displays the total time the program has been running
    print(f"\rCPU Usage: |{cpu_bar}| {cpu_usage:.2f}%   ", end="")
    print(f"RAM Usage: |{mem_bar}| {mem_usage:.2f}%   ", end="\r")
    

while True: #infinte loop until the program is closed
    display_usage(runtime, psutil.cpu_percent(), psutil.virtual_memory().percent, 50) #calls for the procedure to display the bars
    time.sleep(1)
    runtime = runtime + 1 #runtime increase by 1 second every second
    