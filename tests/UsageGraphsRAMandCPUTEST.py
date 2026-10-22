import matplotlib.pyplot as plt  # Imports matplotlib for graphs
from matplotlib.animation import FuncAnimation  # Imports graph animation tools
from collections import deque  # Imports queue data structure
import psutil  # Imports system monitoring tools


cpu_values = deque(maxlen=100)  # Stores the last 100 CPU readings
ram_values = deque(maxlen=100)  # Stores the last 100 RAM readings


fig, (cpu_ax, ram_ax) = plt.subplots(2, 1)  # Creates two graphs stacked vertically


def update(frame):
    cpu_usage = psutil.cpu_percent()  # Gets current CPU usage percentage
    ram_usage = psutil.virtual_memory().percent  # Gets current RAM usage percentage
    cpu_values.append(cpu_usage)  # Adds CPU reading to queue
    ram_values.append(ram_usage)  # Adds RAM reading to queue
    cpu_ax.clear()  # Clears old CPU graph
    ram_ax.clear()  # Clears old RAM graph
    cpu_ax.plot(cpu_values)  # Draws CPU line graph
    ram_ax.plot(ram_values)  # Draws RAM line graph
    cpu_ax.set_ylim(0, 100)  # Limits CPU graph from 0-100%
    ram_ax.set_ylim(0, 100)  # Limits RAM graph from 0-100%
    cpu_ax.set_title("CPU Usage")  # Adds CPU graph title
    ram_ax.set_title("RAM Usage")  # Adds RAM graph title
    cpu_ax.set_ylabel("Usage (%)") # sets name of y-axis
    ram_ax.set_ylabel("Usage (%)") # sets name of y-axis

animation = FuncAnimation(fig, update, interval=1000)  # Updates graphs every second
plt.tight_layout() # adjusts the layout for better spacing

plt.show()  # Displays the graphs