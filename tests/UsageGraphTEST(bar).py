import time 
import psutil # System monitoring library
import matplotlib.pyplot as plt # Plotting tools
from matplotlib.animation import FuncAnimation # animation tools
from collections import deque #queue structure of usage data

cpu_values = deque(maxlen = 50) #length and name of the queue structure, stores 50 (more on deque later)

fig, ax = plt.subplots() # creates graph window and axis

def update(frame):
    cpu_usage = psutil.cpu_percent() # gets % CPU usage from psutil library
    cpu_values.append(cpu_usage) # adds the new reading to the queue
    ax.clear() # clears the last graph to make room for the new one
    ax.bar(range(len(cpu_values)), cpu_values) #creates bar chart from queue data values
    ax.set_ylim(0, 100) # sets y-axis from 0% to 100%
    ax.set_title("CPU Usage") #sets the graph title
    ax.set_ylabel("Usage (%)") # sets name of y-axis
    ax.set_xlabel("Usage Readings") # sets name of x-axis

animation = FuncAnimation(fig, update, interval=1000) # updates graph every 1 second (1000 ms)
plt.show() # displays the graph

# deque is a double ended queue that automatically removes the oldest data element from the
# list when the list is full and a new element is added.
