# •=====• Import libraries •=====• 

from unittest import result
import customtkinter as ctk # used to build the window
import psutil # used to return hardware information
import time
import os
import sys 
import platform # used to return the operating system
from datetime import datetime # used to return the current date and time
import matplotlib.pyplot as plt # used to build the graphs
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg #Makes the graphs compatible with tkinter
from tkinter import colorchooser # used to create the colour chooser
from collections import deque # used to create a queue structure for the graph data
import winreg # used to retrieve the CPU name from the Windows registry
import subprocess # used to run external commands and open external sources
import webbrowser #lets the program open links on the user's default browser
import sqlite3 #Connects SQL databases to the python program


# •=====• Application settings •=====• 


APP_NAME = "Trace" #name of the window and app
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700 


# •=====• Conversion Functions •=====• 


#Simplifying bytes
def byte_to_human(value, suffix="B"): #Psutil will usually return values in bytes, this helps to simpliy the large value
    if value is None:
        return "N/A" #if the value has no value, it will return N/A
    value = float(value) #converts value to a float since it may be a decimal
    for unit in ["", "K", "M", "G", "T", "P"]: #Iterates through the units of byte measurments
        if abs(value) < 1024.0: #If the value is less that 1024, it will return the value with the unit and suffix
            return f"{value:.2f}{unit}{suffix}"
        value /= 1024.0 #If the value is greater than 1024, it will divide the value and continue to the next unit from above, then returns the new value
    return f"{value:.2f}EB"

#Simplifying seconds function
def seconds_to_human(seconds): #Converts seconds to a simpler format
    if seconds is None or seconds < 0: #returns N/A if there is no value or the value is less than 0
        return "N/A"
    seconds = int(seconds) #converts seconds to an integer
    days, remainder = divmod(seconds, 86_400) #divides the seconds by 86,400 (N0. seconds in a day) and returns the remainder
    hours, remainder = divmod(remainder, 3_600) #divides the remainder by  (No. seconds in an hour) and returns the remainder
    minutes, seconds = divmod(remainder, 60) #divides the remainder by 60 (No. seconds in an minute), returns the remaining seconds
    parts = [] #creates an empty list to store days->hours->minutes->seconds, the values below are added to the list if they exist one after another
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts) #returns the final list

# •=====• Extras •=====•

"""

████████╗██████╗░░█████╗░░█████╗░███████╗
╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝
░░░██║░░░██████╔╝███████║██║░░╚═╝█████╗░░
░░░██║░░░██╔══██╗██╔══██║██║░░██╗██╔══╝░░
░░░██║░░░██║░░██║██║░░██║╚█████╔╝███████╗
░░░╚═╝░░░╚═╝░░╚═╝╚═╝░░╚═╝░╚════╝░╚══════╝

open-source device performance monitoring software by Rayaan .S

"""

#Queues for graph data
cpu_values = deque(maxlen=60) #Creates queues for CPU and Memory usage
memory_values = deque(maxlen=60)
storage_values = deque(maxlen=60) #Creates a queue for Storage usage
storage_read_values = deque(maxlen=60)  # Stores read speeds in a queue
storage_write_values = deque(maxlen=60) # Stores write speeds in a queue

#Databases
if getattr(sys, 'frozen', False): #Adjusts based on whether the program is launched from VS Code or the executable
        BASE_DIR = sys._MEIPASS
else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(
    BASE_DIR,
    "data",
    "components.db"
)

def get_database_connection():
    return sqlite3.connect(DB_PATH)
print("Database being used:", DB_PATH) #Checks which database the program is reading






# •=====• Main application •=====• 


class HardwareMonitor(ctk.CTk): # the main class holding all of the reusable code

    def __init__(self):
        super().__init__()

        #Misc
        self.previous_disk_io = psutil.disk_io_counters() #Records a snapshot of the system's current disk input and output counters

        # Window settings
        self.title(APP_NAME) # sets the window title as whatever "APP_NAME" is
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}") # sets the window size as 1100x900px
        self.minsize(900, 600) #creates a minimum window size of 900x600px to keep the sections visble

        # Appearance
        ctk.set_appearance_mode("dark") # sets the default colour scheme as customtkiner's dark-mode
        ctk.set_default_color_theme("dark-blue")

        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create interface (creates the sections for each page or part of the page)
        self.create_sidebar() 
        self.create_dashboard()
        self.create_cpu_page()
        self.create_memory_page()
        self.create_storage_page()
        self.create_settings()

        self.show_dashboard() #Shows dashboard by default when program is opened
        self.update_usage() #updates the CPU and RAM usage %

    #Window closure function (Closes the services the window uses)
        def on_closing(): #Function to close the program when the window is closed
            self.quit() #Destroys the window and closes the program

        self.protocol("WM_DELETE_WINDOW", on_closing) #Calls the on_closing() function when the window is closed, closing all services that the window is using

    #Button colour changer function
    def change_button_colour(self): #Changes the colour of the buttons
        colour =colorchooser.askcolor(title="Choose the colour of your buttons") #Opens the colour changer window
        print(colour)
        if colour[1]: #Takes the hex value of the colour chosen and applies it to the buttons. No colour chosen == no change
            self.dashboard_button.configure(fg_color=colour[1])
            self.settings_button.configure(fg_color=colour[1])
            self.cpu_button.configure(fg_color=colour[1])
            self.memory_button.configure(fg_color=colour[1])
            self.storage_button.configure(fg_color=colour[1])


    #Background theme changer function
    def change_appearance_mode(self, mode): # Function to change the background between light and dark
        ctk.set_appearance_mode(mode)

    #Live value updater function
    def update_usage(self): #Every value within this function is updated every 1000 milliseconds
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent
        storage = psutil.disk_usage("C:\\") #Retrieves the storage usage of the Windows C drive
        used_storage = byte_to_human(storage.used) #Storage being used converted into a suitable format
        storage_percent = int(storage.percent)  #Retrieves the current storage usage as a percentage
        uptime = seconds_to_human(time.time() - psutil.boot_time()) #Calculates the time since the computer was last booted and converts it into a suitable format
        
        ram = psutil.virtual_memory() #Retrieves the RAM usage of the computer
        ram_total = byte_to_human(ram.total) #Total RAM capacity converted into a suitable format
        ram_used = byte_to_human(ram.used) #Used RAM converted into a suitable format
        ram_available = byte_to_human(ram.available) #Available RAM converted into a suitable format

        swap = psutil.swap_memory() #Retrieves the swap memory usage of the computer (virtual memory)
        swap_total = byte_to_human(swap.total) #Total swap memory capacity converted into a suitable format
        swap_used = byte_to_human(swap.used) #Used swap memory converted into a suitable format
        #Memory Labels
        self.ram_amount_label.configure(
            text=f"RAM: {ram_used} / {ram_total}" #Configures the RAM usage label to the detected value
        )
        self.ram_available_label.configure(
            text=f"Available RAM: {ram_available}" #Configures the RAM available label to the detected value
        )
        self.swap_amount_label.configure(
            text=f"Swap: {swap_used} / {swap_total}" #Configures the swap usage label to the detected value
        )

        #Usage queues
        cpu_values.append(cpu_usage) #Adds the new CPU usage value to the queue
        memory_values.append(ram_usage) #Adds the new RAM usage value to the queue

        #Uptime Labels
        self.cpu_uptime_label.configure(
            text=f"Uptime: {uptime}"
        )
        self.memory_uptime_label.configure(
            text=f"Uptime: {uptime}"
        )
        self.storage_uptime_label.configure(
            text=f"Uptime: {uptime}"
        )

        #CPU usage label
        self.cpu_value_label.configure(
            text=f"{cpu_usage}%",
            text_color=self.cpu_usage_colour(cpu_usage)
        )
        #RAM usage label
        self.memory_value_label.configure(
            text=f"{ram_usage}%",
            text_color= self.memory_usage_colour(ram_usage)
        ) #Configures the RAM usage label to the detected value

        #Storage usage label
        total_storage = byte_to_human(storage.total) #Total storage capacity converted into a suitable format
        self.storage_value_label.configure(
            text=f"{used_storage} / {total_storage}", #Ratio of used storage to total storage
            text_color= self.storage_usage_colour(storage_percent)
        )
        self.storage_capacity_label.configure(
            text=f"Capacity: {used_storage} / {total_storage}" #For storage details
        )
        #Configures the storage usage label to the detected value
        #psutil returns storage in bytes, which is why the byte_to_human function is useful in this case.

        # +++++ CPU Details +++++
        key = winreg.OpenKey( 
            winreg.HKEY_LOCAL_MACHINE, #Opens the Windows registry to retrieve the CPU name
            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0" 
        )
        cpu_name = winreg.QueryValueEx(key, "ProcessorNameString")[0] # Retrieves the CPU name from the registry and stores it in cpu_name        
        cpu_info = psutil.cpu_freq() # CPU frequency information
        current_frequency = cpu_info.current # Finds the current frequency of the CPU
        max_frequency = cpu_info.max # Finds the maximum frequency of the CPU
        physical_cores = psutil.cpu_count(logical=False) # Finds the number of physical cores in the CPU
        logical_cores = psutil.cpu_count(logical=True) # Finds the number of logical cores in the CPU
        #Labels
        self.cpu_name_label.configure(
            text=f"CPU: {cpu_name}"
        )
        self.cpu_cores_label.configure(
            text=f"Cores: {physical_cores}"
        )
        self.cpu_logical_cores_label.configure(
            text=f"Logical Cores: {logical_cores}"
        )
        self.cpu_current_frequency_label.configure(
            text=f"Current Frequency: {current_frequency / 1000:.2f} GHz" #Converts the frequency from MHz to GHz and rounds it to 2 decimal places
        )
        self.cpu_max_frequency_label.configure(
            text=f"Max Frequency: {max_frequency / 1000:.2f} GHz" #Converts the frequency from MHz to GHz and rounds it to 2 decimal places
        )

        #Read and write speeds
        # Get current disk activity
        disk_io = psutil.disk_io_counters() #Sets disk_io to the previously stored input and output counter

        # Calculate bytes transferred since the previous update
        read_speed = (
            disk_io.read_bytes - self.previous_disk_io.read_bytes #Subtracts the previous number of read bytes from the current
        ) / 1024 /1024 #Converts bytes/s to MB/s

        write_speed = (
            disk_io.write_bytes - self.previous_disk_io.write_bytes #Subtracts the previous number of written bytes from the current
        ) / 1024 /1024 #Converts bytes/s to MB/s

        #Read/Write labels
        self.disk_read_label.configure(
            text=f"Read Speed: {read_speed:.2f} MB/s" #Sets read speed to 2 decimal places
        )
        self.disk_write_label.configure(
            text=f"Write Speed: {write_speed:.2f} MB/s" #Sets write speed to 2 decimal places
        )
        # Save the counters for the next update
        self.previous_disk_io = disk_io

        #Read/Write Queues
        storage_read_values.append(read_speed)
        storage_write_values.append(write_speed)

        
        self.update_graph() #Updates the graph with new values
        self.update_cpu_graph() #Updates the CPU graph with new values
        self.update_memory_graph() #Updates the Memory graph with new values
        self.update_storage_graph() #Updates the Storage graph with new values
        
        self.after(1000, self.update_usage) #Updates all labels within this function every 1000 milliseconds



    #Graph updater function
    def update_graph(self): #Updates the graph with new values
        self.ax.clear() #Clears the graph to make room for the new values

        if ctk.get_appearance_mode() =="Dark": #Checks if the app is in dark mode or light mode, changed the colours of the graph depending on the theme
            self.ax.set_facecolor("#222222") #Sets the background colour of the graph to a dark grey
            self.figure.patch.set_facecolor("#2b2b2b")
            self.ax.tick_params(colors="white") #Sets the colour of the tick marks to white
            self.ax.xaxis.label.set_color("white") #Sets the colours of the axis labels to white
            self.ax.yaxis.label.set_color("white")
            self.ax.title.set_color("white") #Sets the colour of the graph title to white 
        else:  
            self.ax.set_facecolor("white") #Sets the background colour of the graph to white
            self.figure.patch.set_facecolor("white")
            self.ax.tick_params(colors="black") #Sets the colour of the tick marks to black
            self.ax.xaxis.label.set_color("black") #Sets the colours of the axis labels to black
            self.ax.yaxis.label.set_color("black")
            self.ax.title.set_color("black") #Sets the colour of the graph title to black

        self.ax.plot(cpu_values, label="CPU") #Labels the CPU usage line on the graph
        self.ax.plot(memory_values, label="Memory") #Labels the Memory usage line on the graph

        self.ax.set_ylim(0, 100)
        self.ax.set_ylabel("Usage (%)") #Sets the y-axis label to "Usage (%)"
        self.ax.set_xlabel("Time (s)") #Sets the x-axis label to "Time" since the graph is updated every second
        self.ax.set_title("System Usage") #Sets the graph title to "System Usage"

        self.ax.legend() #Adds a legend to the graph to indicate which line is CPU and which is Memory

        self.canvas.draw() #Creates the graph
    
    
    #Returns the usage status based on the percentage usages
    def cpu_usage_colour(self, cpu_usage):
        if cpu_usage <= 50:
            return "green" #returns green if usage is below or equal to 50%
        elif 50 < cpu_usage <= 80:
            return "orange" #returns orange is usage is above 50% and below or equal to 80%
        else:
            return "red" #Any other usage reading returns red

    def memory_usage_colour(self, ram_usage):
            if ram_usage <= 50:
                return "green" #returns green if usage is below or equal to 50%
            elif 50 < ram_usage <= 80:
                return "orange" #returns orange is usage is above 50% and below or equal to 80%
            else:
                return "red" #Any other usage reading returns red

    def storage_usage_colour(self, storage_percent):
                if storage_percent <= 50:
                    return "green" #returns green if usage is below or equal to 50%
                elif 50 < storage_percent <= 90:
                    return "orange" #returns orange is usage is above 50% and below or equal to 90%
                else:
                    return "red" #Any other usage reading returns red

    #Update Graphs
    def update_cpu_graph(self):
        self.cpu_ax.clear()
        
    # Check current app appearance
        if ctk.get_appearance_mode() == "Dark": #Checks if the app is in dark mode or light mode, changed the colours of the graph depending on the theme
            background = "#222222"
            text = "white"
        else:
            background = "white"
            text = "black"

    # Set graph colours
        self.cpu_figure.patch.set_facecolor(background) #Sets the background colour of the graph to a dark grey
        self.cpu_ax.set_facecolor(background) #Sets the background colour of the graph to a dark grey

        self.cpu_ax.tick_params(colors=text)
        self.cpu_ax.xaxis.label.set_color(text)
        self.cpu_ax.yaxis.label.set_color(text)
        self.cpu_ax.title.set_color(text)

        self.cpu_ax.plot(cpu_values) #Plots the CPU usage values on the graph

        self.cpu_ax.set_ylim(0, 100) # Sets the y-axis limit to 0-100 since the CPU usage is a percentage
        self.cpu_ax.set_ylabel("Usage (%)")
        self.cpu_ax.set_xlabel("Time")
        self.cpu_ax.set_title("CPU Usage")

        self.cpu_canvas.draw()

    def update_memory_graph(self):
            self.memory_ax.clear()
            
        # Check current app appearance
            if ctk.get_appearance_mode() == "Dark": #Checks if the app is in dark mode or light mode, changed the colours of the graph depending on the theme
                background = "#222222"
                text = "white"
            else:
                background = "white"
                text = "black"
    
        # Set graph colours
            self.memory_figure.patch.set_facecolor(background) #Sets the background colour of the graph to a dark grey
            self.memory_ax.set_facecolor(background) #Sets the background colour of the graph to a dark grey
    
            self.memory_ax.tick_params(colors=text)
            self.memory_ax.xaxis.label.set_color(text)
            self.memory_ax.yaxis.label.set_color(text)
            self.memory_ax.title.set_color(text)
    
            self.memory_ax.plot(memory_values) #Plots the memory usage values on the graph
    
            self.memory_ax.set_ylim(0, 100) # Sets the y-axis limit to 0-100 since the memory usage is a percentage
            self.memory_ax.set_ylabel("Usage (%)")
            self.memory_ax.set_xlabel("Time")
            self.memory_ax.set_title("Memory Usage")
    
            self.memory_canvas.draw()


    def update_storage_graph(self):
        self.storage_ax.clear()  # Clears the previous graph

        # Detect the app's appearance mode to change graph colours
        if ctk.get_appearance_mode() == "Dark":
            background = "#222222"
            text = "white"
        else:
            background = "white"
            text = "black"

        # Apply theme colours
        self.storage_figure.patch.set_facecolor(background)
        self.storage_ax.set_facecolor(background)
        self.storage_ax.tick_params(colors=text)
        self.storage_ax.xaxis.label.set_color(text)
        self.storage_ax.yaxis.label.set_color(text)
        self.storage_ax.title.set_color(text)

        for spine in self.storage_ax.spines.values():
            spine.set_color(text)

        # Plot read and write speeds
        self.storage_ax.plot(
            storage_read_values,
            label="Read Speed"
        )
        self.storage_ax.plot(
            storage_write_values,
            label="Write Speed"
        )
        # Label the graph
        self.storage_ax.set_ylabel("Speed (MB/s)")
        self.storage_ax.set_xlabel("Time (seconds)")
        self.storage_ax.set_title("Storage Read/Write Speeds")

        # Keep the speed scale starting at zero
        self.storage_ax.set_ylim(bottom=0)

        # Display the line names
        legend = self.storage_ax.legend()
        legend.get_frame().set_facecolor(background)

        for label in legend.get_texts():
            label.set_color(text)

        self.storage_canvas.draw()

    def get_memory_details(self): #Will contain the subprocesses to retreive memory details
    #RAM form Type (DIMM or SODIMM)
        result = subprocess.run(
            [
                "powershell", #Where the command is being run, in this case powershell
                "-Command",
                "Get-CimInstance Win32_PhysicalMemory | Select-Object -ExpandProperty FormFactor" #Powershell Command, returns a number
            ],
            capture_output=True, #Captures the output of the command
            text=True #Converts the output to text so it can be read and used in the program
        )
        form_factor = result.stdout.strip().splitlines()[0] # Strips any leading or trailing whitespace from the output
        print("Raw value:", repr(form_factor)) #Prints the raw value of the form factor for debugging purposes
        #Convert the number into a readable name
        form_factors = {
            "8": "DIMM",
            "12": "SODIMM"
        }
        form_factor_names = [
            form_factors.get(form_factor, "Unknown")
        ]
        form_factor = " / ".join(form_factor_names) #Sets the form factor to the corresponding name, if the number is not in the dictionary, it will return "Unknown"
        #Puts a / between each value in the case that there is more than one stick installed

        result = subprocess.run( #DDR generation of the RAM
            [
                "powershell",
                "-Command",
                "Get-CimInstance Win32_PhysicalMemory | Select-Object -ExpandProperty SMBIOSMemoryType" #Returns a number corresponding to the DDR generation
            ],
            capture_output=True,
            text=True
        )
        memory_type_values = result.stdout.strip().splitlines() #Splits the output into a list of lines, in case there is more than one stick of RAM installed
        print("Raw value:", repr(memory_type_values)) #Prints the raw value of the memory type for debugging purposes
        memory_types = {
            "20": "DDR",
            "21": "DDR2",
            "24": "DDR3",
            "26": "DDR4",
            "34": "DDR5"
        }
        memory_type_names = [
            memory_types.get(value, "Unknown")
            for value in memory_type_values
        ]
        memory_type = " / ".join(memory_type_names) #Sets the memory type to the corresponding DDR generation, if the number is not in the dictionary, it will return "Unknown"
        #Puts a / between each value in the case that there is more than one stick installed

    #RAM Slots
        result = subprocess.run( #Return number of occupied slots
            [
                "powershell",
                "-Command",
                "(Get-CimInstance Win32_PhysicalMemory).Count" #Powershell command, returns the number of RAM slots occupied
            ],
            capture_output=True,
            text=True
        )
        used_slots = result.stdout.strip() # Strips any leading or trailing whitespace from the output
        result = subprocess.run( #Return the total slots
            [
                "powershell",
                "-Command",
                "(Get-CimInstance Win32_PhysicalMemoryArray).MemoryDevices" #Powershell command, returns the number of RAM slots on the motherboard
            ],
            capture_output=True,
            text=True
        )
        total_slots = result.stdout.strip() # Strips any leading or trailing whitespace from the output
        print("Total slots:", repr(total_slots))
        print("Used slots:", repr(used_slots)) #Debugging purposes, prints the number of total and used slots to the console
    #Labels
        self.ram_form_factor_label.configure(
            text=f"Form Factor: {form_factor}"
        )

        self.ram_type_label.configure(
            text=f"RAM Type: {memory_type}"
        )

        self.ram_slots_label.configure(
            text=f"RAM Slots: {used_slots} / {total_slots}"
        )
    def get_storage_details(self):
        result = subprocess.run( #Returns the type of secondary storage
            [
                "powershell", #Where the command will be run
                "-Command",
                "Get-PhysicalDisk | Select-Object -ExpandProperty MediaType" #Powershell command, returns the media type of the storage device
            ],
            capture_output=True,
            text=True
        )
        storage_type_values = result.stdout.strip().splitlines() #Splits the output into a list of lines, in case there is more than one storage device installed
        print("Raw value:", repr(storage_type_values)) #Prints the raw value of the media type for debugging purposes
        media_types = {
            "HDD": "HDD",
            "SSD": "SSD",
            "Unspecified": "Unknown"
        }
        storage_type_names = [
            media_types.get(value, "Unknown")
            for value in storage_type_values
        ]
        storage_type = " / ".join(storage_type_names) #Sets the media type to the corresponding name, if the value is not in the dictionary, it will return "Unknown"
        #Puts a / between each value in the case that there is more than one storage device installed
        #Creates the label for the type of storage
        self.storage_type_label.configure(
            text = f"Storage Type: {storage_type}"
        )
        #Drive name
        result = subprocess.run( #Subprocess to return the name of the storage device
        [
            "powershell",
            "-Command",
            "Get-PhysicalDisk | Select-Object -ExpandProperty FriendlyName" #Command to put in terminal
        ],
        capture_output=True,
        text=True
        )
        storage_name = result.stdout.strip()
        print("Storage name:", storage_name) #Outputs the name of the storage media into terminal for debugging purposes
        #Drive name label
        self.storage_name_label.configure(
            text=f"Drive: {storage_name}"
        )

    #Storage Database
    def open_storage_database(self): #Function to open a new scrollable window to display the records in the storage tables
        print("Storage upgrade database selected")
        database_window = ctk.CTkToplevel(self)
        database_window.title("Storage Upgrade Database") #Sets the title of the window
        database_window.geometry("900x650")

        title = ctk.CTkLabel(
            database_window,
            text="Storage Upgrade Database", #Adds a title
            font=("Arial", 24, "bold")
        )
        title.pack(pady=(20, 10))

        storage_type = ctk.StringVar(value="Desktop")

        storage_dropdown = ctk.CTkComboBox( #Creates a box that allows the user to choose between the desktop table or the laptop table
            database_window,
            values=["Desktop", "Laptop"], #Lists options
            variable=storage_type,
            command=lambda choice: load_storage(choice)
        )
        storage_dropdown.pack(pady=(0, 15))

        scroll_frame = ctk.CTkScrollableFrame( #Creates the scrollable frame on the tkinter window
            database_window,
            width=820,
            height=480
        )
        scroll_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        def load_storage(choice):
            for widget in scroll_frame.winfo_children():
                widget.destroy()

            if choice == "Desktop":   #Takes the selected option in the dropdown menu to select a table
                table_name = "DesktopStorage"
            else:
                table_name = "LaptopStorage"

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT brand, model, capacity_gb, drive_type,
                        form_factor, interface, read_mbs,
                        write_mbs, price_gbp, product_url
                FROM {table_name}
                ORDER BY price_gbp DESC
            """) #SQL statement to return the records is price descending order

            records = cursor.fetchall()
            conn.close()

            for record in records:
                brand, model, capacity, drive_type, form_factor, interface, read_speed, write_speed, price, product_url = record

                if price is None:
                    price_text = "Price unavailable"
                else:
                    price_text = f"£{price:.2f}"

                record_text = (
                    f"{brand} {model}\n"
                    f"Capacity: {capacity}GB\n"
                    f"Type: {drive_type}\n"
                    f"Form Factor: {form_factor}\n"
                    f"Interface: {interface}\n"
                    f"Read: {read_speed} MB/s\n"
                    f"Write: {write_speed} MB/s\n"
                    f"Price: {price_text}\n"
                    f"Link: {product_url}"
                ) #Format the attributes will be displayed in

                record_label = ctk.CTkLabel(
                    scroll_frame,
                    text=record_text,
                    anchor="w",
                    justify="left",
                    font=("Arial", 14)
                )
                record_label.pack(
                    fill="x",
                    padx=10,
                    pady=10
                )

        load_storage("Desktop")

    #CPU Database
    def open_cpu_database(self):
        database_window = ctk.CTkToplevel(self)
        database_window.title("CPU Upgrade Database")
        database_window.geometry("900x650")

        title = ctk.CTkLabel(
            database_window,
            text="CPU Upgrade Database",
            font=("Arial", 24, "bold")
        )
        title.pack(pady=(20, 10))

        scroll_frame = ctk.CTkScrollableFrame(
            database_window,
            width=820,
            height=520
        )
        scroll_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT brand, model, cores, threads,
                    base_ghz, boost_ghz, socket, price_gbp, product_url
            FROM CPUs
            ORDER BY price_gbp DESC
        """)#SQL statement

        records = cursor.fetchall() #Returns all records
        print("CPU records returned:", len(records)) #For debugging
        conn.close()

        for record in records:
            brand, model, cores, threads, base_speed, boost_speed, socket, price, product_url = record

            if price is None:
                price_text = "Price unavailable"
            else:
                price_text = f"£{price:.2f}"

            record_frame = ctk.CTkFrame(
                scroll_frame
            )
            record_frame.pack(
                fill="x",
                padx=10,
                pady=5
            )

            record_text = (
                f"{brand} {model}\n"
                f"Cores: {cores} | Threads: {threads}\n"
                f"Base Clock: {base_speed} GHz\n"
                f"Boost Clock: {boost_speed} GHz\n"
                f"Socket: {socket}\n"
                f"Price: {price_text}\n"
                f"Link: {product_url}"
            ) #Format of attributes

            record_label = ctk.CTkLabel(
                record_frame,
                text=record_text,
                anchor="w",
                justify="left",
                font=("Arial", 14)
            )
            record_label.pack(
                fill="x",
                padx=15,
                pady=10
            )

    #Memory Database
    def open_memory_database(self):
        print("Memory upgrade database selected")
        database_window = ctk.CTkToplevel(self)
        database_window.title("Memory Upgrade Database")
        database_window.geometry("900x650")

        title = ctk.CTkLabel(
            database_window,
            text="Memory Upgrade Database",
            font=("Arial", 24, "bold")
        )
        title.pack(pady=(20, 10))

        memory_type = ctk.StringVar(value="Desktop")

        memory_dropdown = ctk.CTkComboBox(
            database_window,
            values=["Desktop", "Laptop"],
            variable=memory_type,
            command=lambda choice: load_memory(choice)
        )
        memory_dropdown.pack(pady=(0, 15))

        scroll_frame = ctk.CTkScrollableFrame(
            database_window,
            width=820,
            height=480
        )
        scroll_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        def load_memory(choice):
            for widget in scroll_frame.winfo_children():
                widget.destroy()

            if choice == "Desktop":
                table_name = "RAM"
            else:
                table_name = "LaptopRAM"

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT brand, model, capacity_gb, configuration,
                        ddr_generation, speed_mts, form_factor,
                        cas_latency, price_gbp, product_url
                FROM {table_name}
                ORDER BY price_gbp DESC
            """)

            records = cursor.fetchall()
            conn.close()

            for record in records:
                brand, model, capacity, configuration, ddr, speed, form_factor, cas, price, product_url = record

                if price is None:
                    price_text = "Price unavailable"
                else:
                    price_text = f"£{price:.2f}"

                record_text = (
                    f"{brand} {model}\n"
                    f"Capacity: {capacity}GB ({configuration})\n"
                    f"Generation: {ddr}\n"
                    f"Speed: {speed} MT/s\n"
                    f"Form Factor: {form_factor}\n"
                    f"CAS Latency: CL{cas}\n"
                    f"Price: {price_text}\n"
                    f"Link: {product_url}"
                )

                record_label = ctk.CTkLabel(
                    scroll_frame,
                    text=record_text,
                    anchor="w",
                    justify="left",
                    font=("Arial", 14)
                )
                record_label.pack(
                    fill="x",
                    padx=10,
                    pady=10
                )

        load_memory("Desktop")











# •=====• Sidebar •=====• 


    def create_sidebar(self):

        self.sidebar = ctk.CTkFrame(
            self,
            width=220, # keeps the sidebar slim so there will be enough room for the other sections
            corner_radius=0
        )

        self.sidebar.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.sidebar.grid_propagate(False)

        # Application title
        self.logo = ctk.CTkLabel( # sets the title name at the top of the sidebar to the app name
            self.sidebar,
            text="Trace",
            font=ctk.CTkFont(
                size=35,
                weight="bold"
            )
        )

        self.logo.pack(
            padx=20,
            pady=(30, 40)
        )

        # Navigation buttons
        self.dashboard_button = ctk.CTkButton( # creates a button
            self.sidebar,
            text="Dashboard", # sets the text in the button to "Dashboard"
            command=self.show_dashboard # executes the code int the show_dashboard(self) function
        )

        self.dashboard_button.pack( # sets the size of the dashboard button
            padx=20,
            pady=5,
            fill="x"
        )
        
        #The rest of the buttons have a very similar format of code since they are all so similar

        self.cpu_button = ctk.CTkButton(
            self.sidebar,
            text="CPU",
            command=self.show_CPU
        )

        self.cpu_button.pack(
            padx=20,
            pady=5,
            fill="x"
        )

        self.memory_button = ctk.CTkButton(
            self.sidebar,
            text="Memory",
            command=self.show_memory
        )

        self.memory_button.pack(
            padx=20,
            pady=5,
            fill="x"
        )

        self.storage_button = ctk.CTkButton(
            self.sidebar,
            text="Storage",
            command=self.show_storage
        )

        self.storage_button.pack(
            padx=20,
            pady=5,
            fill="x"
        )

        # Settings at bottom (uses the same code for the rest of the buttons, except the "side='bottom'" part)
        self.settings_button = ctk.CTkButton(
            self.sidebar,
            text="Settings",
            command=self.show_settings
        )

        self.settings_button.pack(
            side="bottom", # puts the button on the bottom of the sidebar
            padx=20,
            pady=25, # creates some room around the button so its more centered
            fill="x"
        )


# •=====• Dashboard •=====•

    def create_dashboard(self):

        self.dashboard = ctk.CTkFrame( # Creates the main section for the dashboard
            self,
            corner_radius=0,
            fg_color="transparent"
        )

        self.dashboard.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=30,
            pady=30
        )

        self.dashboard.grid_columnconfigure( #Creates the columns on the dashboard
            (0, 1, 2),
            weight=1
        )

        self.dashboard.grid_rowconfigure( #Creats one row for the information cards and another for the graph
            2,
            weight=1
        )

        # Dashboard heading (sets the text at the top of the dashboard section to "Dashboard")
        self.heading = ctk.CTkLabel( 
            self.dashboard,
            text="Dashboard",
            font=ctk.CTkFont(
                size=30,
                weight="bold" # Makes the heading larger and bold to stand out from other text
            )
        )

        self.heading.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 5)
        )

        # Subtitle (Creates a very short description under the heading)
        self.subtitle = ctk.CTkLabel(
            self.dashboard,
            text="Monitor your system performance",
            font=ctk.CTkFont(size=15) # The subtitle text should be smaller than the heading's
        )

        self.subtitle.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 25)
        )

        # Information cards
        self.cpu_value_label = self.create_card( # Uses the create_card() function below to build 4 information cards that can display hardware values
            "CPU Usage", #Labels the card as "CPU_Usage"
            f"{psutil.cpu_percent()}%",
            0
        )

        self.memory_value_label = self.create_card(
            "Memory Usage", #Labels the card as "Memory_Usage"
            f"{psutil.virtual_memory().percent}%",
            1
        )

        self.storage_value_label =self.create_card(
            "Storage", # Labels the card as "Storage" 
            f"{byte_to_human(psutil.disk_usage("C:\\").total)}", #Returns the size of the Window's "C://" disk and uses the bytes_to_human function to simplify the value.
            #(Only windows uses a C:// drive, so this will not work on other operating systems)
            2
        )

        # Graph frame
        self.graph_frame = ctk.CTkFrame(
            self.dashboard,
            height=300
        )

        self.graph_frame.grid( #Creates the frame where the graphs will go
            row=3,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(25, 0)
        )
        
        #Create the graph
        self.figure, self.ax = plt.subplots() # Creates a figure and the axes for the graph

        self.canvas = FigureCanvasTkAgg( # Makes the graph compatible with tkinter
            self.figure,
            master=self.graph_frame #Puts the graph in the designated frame on the dashboard
        )

        self.canvas.get_tk_widget().grid( # Places the graph in the frame, setting its size and position
            row=0,
            column=0,
            sticky="nsew",
            padx=10,
            pady=10
        )

        self.graph_frame.grid_propagate(False) #Stops the graph from resizing itself

        self.graph_frame.grid_columnconfigure(0, weight=1) #Expands the graph to fill the frame
        self.graph_frame.grid_rowconfigure(0, weight=1)



# •=====• Information cards •=====•


    def create_card(self, title, value, column): #Builds the information cards that go into the dashboard

        card = ctk.CTkFrame(
            self.dashboard,
            height=130
        )

        card.grid(
            row=2,
            column=column,
            sticky="nsew",
            padx=5
        )

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=15)
        )

        title_label.pack(
            anchor="w",
            padx=20,
            pady=(20, 5)
        )

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(
                size=28,
                weight="bold"
            )
        )

        value_label.pack(
            anchor="w",
            padx=20
        )
        return value_label


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Component Pages (CPU, Memory, Storage)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



# •=====• CPU •=====• 


    def create_cpu_page(self):
        self.cpu_page = ctk.CTkFrame( #Creates the page for the CPU
            self,
            corner_radius=0,
            fg_color="transparent"
        )

        self.cpu_page.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=30,
            pady=30
        )
        #Resizing the page
        self.cpu_page.grid_columnconfigure(0, weight=1)
        self.cpu_page.grid_columnconfigure(1, weight=1)
        self.cpu_page.grid_rowconfigure(0, weight=3)
        self.cpu_page.grid_rowconfigure(1, weight=2)

        #Page title
        self.cpu_title = ctk.CTkLabel(
            self.cpu_page,
            text="CPU",
            font=ctk.CTkFont(size=30, weight="bold")
        )
        self.cpu_title.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 15)
        )

        # Graph section
        self.cpu_graph_frame = ctk.CTkFrame(self.cpu_page) #Creates and empty section for the graph
        self.cpu_graph_frame.grid( 
            row=1,
            column=0,
            columnspan=2,
            sticky="nsew",
            pady=(0, 20)
        )

        self.cpu_figure, self.cpu_ax = plt.subplots() #Creates a figure and axes for the graph
        self.cpu_canvas = FigureCanvasTkAgg(
            self.cpu_figure,
            master=self.cpu_graph_frame #Puts the graph in the designated frame on the CPU page
        )
        self.cpu_canvas.get_tk_widget().grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.cpu_graph_frame.grid_propagate(False) #Stops the graph from resizing itself
        
        self.cpu_graph_frame.grid_columnconfigure(0, weight=1) #Expands the graph to fill the frame
        self.cpu_graph_frame.grid_rowconfigure(0, weight=1)

        # Buttons section
        self.cpu_button_frame = ctk.CTkFrame(self.cpu_page) #Creates the frame that holds the buttons within the page
        self.cpu_button_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )
        self.cpu_info_button = ctk.CTkButton( #Button that opens an external source that can help the user learn more about the component
            self.cpu_button_frame,
            text="Learn About CPUs",
            command=self.open_cpu_info
        )
        self.cpu_info_button.grid(
            row=0,
            column=0,
            padx=20,
            pady=(20, 10),
            sticky="ew"
        )
        self.cpu_database_button = ctk.CTkButton( #Button that opens the database of CPUs at different price ranges
            self.cpu_button_frame,
            text="CPU Upgrade Database",
            command=self.open_cpu_database
        )
        self.cpu_database_button.grid(
            row=1,
            column=0,
            padx=20,
            pady=10,
            sticky="ew"
        )
        self.cpu_button_frame.grid_columnconfigure(0, weight=1) #Makes the buttons expand to fill the frame
        
        #Uptime label (Shows the time since the computer was last booted)
        self.cpu_uptime_label = ctk.CTkLabel( #Refers to the label in update_usage()
            self.cpu_button_frame,
            text="Uptime: 0 days, 0 hours", #Ignore
            font=ctk.CTkFont(size=25, weight="bold") #Sets the format of the text
        )
        self.cpu_uptime_label.grid(
            row=2,
            column=0,
            padx=20,
            pady=(15, 10),
            sticky="w"
        )

        # +++++++ Details section +++++++
        self.cpu_details_frame = ctk.CTkFrame(self.cpu_page) # Creates the frame that will hold additional details about the component
        self.cpu_details_frame.grid(
            row=2,
            column=1,
            sticky="nsew",
            padx=(10, 0)
        )

        self.cpu_name_label = ctk.CTkLabel(
            self.cpu_details_frame,
            text="CPU: Loading...", #Displays the name of the CPU
            font=ctk.CTkFont(size=15)
        )
        self.cpu_name_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=10
        )

        self.cpu_cores_label = ctk.CTkLabel(
            self.cpu_details_frame,
            text="Cores: Loading...",
            font=ctk.CTkFont(size=15)
        )
        self.cpu_cores_label.grid(
            row=1,
            column=0,
            sticky="w",
            padx=20,
            pady=10
        )

        self.cpu_logical_cores_label = ctk.CTkLabel(
            self.cpu_details_frame,
            text="Logical Cores: Loading...",
            font=ctk.CTkFont(size=15)
        )
        self.cpu_logical_cores_label.grid(
            row=2,
            column=0,
            sticky="w",
            padx=20,
            pady=10
        )

        self.cpu_current_frequency_label = ctk.CTkLabel(
            self.cpu_details_frame,
            text="Current Frequency: Loading...",
            font=ctk.CTkFont(size=15)
        )
        self.cpu_current_frequency_label.grid(
            row=3,
            column=0,
            sticky="w",
            padx=20,
            pady=10
        )

        self.cpu_max_frequency_label = ctk.CTkLabel(
            self.cpu_details_frame,
            text="Max Frequency: Loading...",
            font=ctk.CTkFont(size=15)
        )
        self.cpu_max_frequency_label.grid(
            row=4,
            column=0,
            sticky="w",
            padx=20,
            pady=10
        )

# •=====• Memory  •=====• 
# (Same format as cpu_page())


    def create_memory_page(self):
        self.memory_page = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color="transparent"
        )

        self.memory_page.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=30,
            pady=30
        )
        #Resizing the page
        self.memory_page.grid_columnconfigure(0, weight=1)
        self.memory_page.grid_columnconfigure(1, weight=1)
        self.memory_page.grid_rowconfigure(0, weight=3)
        self.memory_page.grid_rowconfigure(1, weight=2)

        #Page title
        self.memory_title = ctk.CTkLabel(
            self.memory_page,
            text="Memory",
            font=ctk.CTkFont(size=30, weight="bold")
        )
        self.memory_title.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 15)
        )

        # Graph section
        self.memory_graph_frame = ctk.CTkFrame(self.memory_page)
        self.memory_graph_frame.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="nsew",
            pady=(0, 20)
        )
        
        self.memory_figure, self.memory_ax = plt.subplots() #Creates a figure and axes for the graph
        self.memory_canvas = FigureCanvasTkAgg(
            self.memory_figure,
            master=self.memory_graph_frame #Puts the graph in the designated frame on the Memory page
        )
        self.memory_canvas.get_tk_widget().grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.memory_graph_frame.grid_propagate(False) #Stops the graph from resizing itself
        
        self.memory_graph_frame.grid_columnconfigure(0, weight=1) #Expands the graph to fill the frame
        self.memory_graph_frame.grid_rowconfigure(0, weight=1)

        # Buttons section
        self.memory_button_frame = ctk.CTkFrame(self.memory_page)
        self.memory_button_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )
        self.memory_info_button = ctk.CTkButton( #Button that opens an external source that can help the user learn more about the component
            self.memory_button_frame,
                text="Learn About Memory", #Text within the button
                command=self.open_memory_info #Calls the function to do what the button is supposed to do when pressed
        )
        self.memory_info_button.grid(
            row=0,
            column=0,
            padx=20,
            pady=(20, 10),
                sticky="ew"
        )
        self.memory_database_button = ctk.CTkButton( #Button that opens the database of CPUs at different price ranges
            self.memory_button_frame,
            text="Memory Upgrade Database", #Text within the button
            command=self.open_memory_database #Calls the function to do what the button is supposed to do when pressed
        )
        self.memory_database_button.grid(
            row=1,
            column=0,
            padx=20,
            pady=10,
            sticky="ew"
        )
        self.memory_button_frame.grid_columnconfigure(0, weight=1) #Makes the buttons expand to fill the frame

        #Uptime label (Shows the time since the computer was last booted)
        self.memory_uptime_label = ctk.CTkLabel( #Refers to the label in update_usage()
            self.memory_button_frame,
            text="Uptime: 0 days, 0 hours", #Ignore
            font=ctk.CTkFont(size=25, weight="bold") #Sets the format of the text
        )
        self.memory_uptime_label.grid(
            row=2,
            column=0,
            padx=20,
            pady=(15, 10),
            sticky="w"
        )

        # Details section
        self.memory_details_frame = ctk.CTkFrame(self.memory_page)
        self.memory_details_frame.grid(
            row=2,
            column=1,
            sticky="nsew",
            padx=(10, 0)
        )

        self.ram_amount_label = ctk.CTkLabel(
            self.memory_details_frame,
            text="RAM: Loading...", #Displays the amount of the RAM
            font=ctk.CTkFont(size=15)
        )
        self.ram_amount_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=10
        )
        self.ram_available_label = ctk.CTkLabel(
            self.memory_details_frame,
            text="RAM Available: Loading...", #Displays the available RAM
            font=ctk.CTkFont(size=15)
        )
        self.ram_available_label.grid(
            row=1,
            column=0,
            sticky="w",
            padx=20,
            pady=10
        )
        self.swap_amount_label = ctk.CTkLabel(
            self.memory_details_frame,
            text="Swap: Loading...", #Displays the amount of swap memory
            font=ctk.CTkFont(size=15)
        )
        self.swap_amount_label.grid(
            row=2,
            column=0,
            sticky="w",
            padx=20,
            pady=10
        )
        self.ram_form_factor_label = ctk.CTkLabel(
            self.memory_details_frame,
            text="RAM Form Factor: Loading...", #Displays the form factor of the RAM
            font=ctk.CTkFont(size=15)
        )
        self.ram_form_factor_label.grid(
            row=3,
            column=0,
            sticky="w",
            padx=20,
            pady=10
        )
        self.ram_type_label = ctk.CTkLabel(
            self.memory_details_frame,
            text="RAM Type: Loading...", #Displays the type of the RAM
            font=ctk.CTkFont(size=15)
        )
        self.ram_type_label.grid(
            row=4,
            column=0,
            sticky="w",
            padx=20,
            pady=10
        )
        self.ram_slots_label = ctk.CTkLabel(
            self.memory_details_frame,
            text="RAM Slots: Loading...", #Displays the number of RAM slots
            font=ctk.CTkFont(size=15)
        )
        self.ram_slots_label.grid(
            row=5,
            column=0,
            sticky="w",
            padx=20,
            pady=10
        )
        self.get_memory_details() #Calls the function to get the memory details and display them on the page


# •=====• Storage •=====• 
# (Same format as cpu_page())


    def create_storage_page(self):
        self.storage_page = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color="transparent"
        )

        self.storage_page.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=30,
            pady=30
        )

        #Resizing the page
        self.storage_page.grid_columnconfigure(0, weight=1)
        self.storage_page.grid_columnconfigure(1, weight=1)
        self.storage_page.grid_rowconfigure(0, weight=3)
        self.storage_page.grid_rowconfigure(1, weight=2)

        #Page title
        self.storage_title = ctk.CTkLabel(
            self.storage_page,
            text="Storage",
            font=ctk.CTkFont(size=30, weight="bold")
        )
        self.storage_title.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 15)
        )

        # Graph section
        self.storage_graph_frame = ctk.CTkFrame(self.storage_page)
        self.storage_graph_frame.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="nsew",
            pady=(0, 20)
        )
        
        self.storage_figure, self.storage_ax = plt.subplots() #Creates a figure and axes for the graph
        self.storage_canvas = FigureCanvasTkAgg(
            self.storage_figure,
            master=self.storage_graph_frame #Puts the graph in the designated frame on the Storage page
        )
        self.storage_canvas.get_tk_widget().grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.storage_graph_frame.grid_propagate(False) #Stops the graph from resizing itself
        
        self.storage_graph_frame.grid_columnconfigure(0, weight=1) #Expands the graph to fill the frame
        self.storage_graph_frame.grid_rowconfigure(0, weight=1)

        # Buttons section
        self.storage_button_frame = ctk.CTkFrame(self.storage_page)
        self.storage_button_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )
        self.storage_info_button = ctk.CTkButton( #Button that opens an external source that can help the user learn more about the component
            self.storage_button_frame,
            text="Learn About Storage", #Text within the button
            command=self.open_storage_info #Calls the function to do what the button is supposed to do when pressed
        )
        self.storage_info_button.grid(
            row=0,
            column=0,
            padx=20,
            pady=(20, 10),
                sticky="ew"
        )
        self.storage_database_button = ctk.CTkButton( #Button that opens the database of CPUs at different price ranges
            self.storage_button_frame,
            text="Storage Upgrade Database", #Text within the button
            command=self.open_storage_database #Calls the function to do what the button is supposed to do when pressed
        )
        self.storage_database_button.grid(
            row=1,
            column=0,
            padx=20,
            pady=10,
            sticky="ew"
        )
        self.storage_button_frame.grid_columnconfigure(0, weight=1) #Makes the buttons expand to fill the frame

        #Uptime label (Shows the time since the computer was last booted)
        self.storage_uptime_label = ctk.CTkLabel( #Refers to the label in update_usage()
            self.storage_button_frame,
            text="Uptime: 0 days, 0 hours", #Ignore
            font=ctk.CTkFont(size=25, weight="bold") #Sets the format of the text
        )
        self.storage_uptime_label.grid(
            row=2,
            column=0,
            padx=20,
            pady=(15, 10),
            sticky="w"
        )

        # Details section
        self.storage_details_frame = ctk.CTkFrame(self.storage_page)
        self.storage_details_frame.grid(
            row=2,
            column=1,
            sticky="nsew",
            padx=(10, 0)
        )
        self.storage_name_label = ctk.CTkLabel(
            self.storage_details_frame,
            text="Drive: Loading..."
        )
        self.storage_name_label.grid(
            row=0, column=0, sticky="w", padx=10, pady=5
        )
        self.storage_type_label = ctk.CTkLabel(
            self.storage_details_frame,
            text="Storage Type: Loading..."
        )
        self.storage_type_label.grid(
            row=1, column=0, sticky="w", padx=10, pady=5
        )
        self.disk_read_label = ctk.CTkLabel(
            self.storage_details_frame,
            text="Read Speed: Loading..."
        )
        self.disk_read_label.grid(
            row=2, column=0, sticky="w", padx=10, pady=5
        )
        self.disk_write_label = ctk.CTkLabel(
            self.storage_details_frame,
            text="Write Speed: Loading..."
        )
        self.disk_write_label.grid(
            row=3, column=0, sticky="w", padx=10, pady=5
        )
        self.storage_capacity_label = ctk.CTkLabel(
            self.storage_details_frame,
            text="Capacity: Loading..."
        )
        self.storage_capacity_label.grid(
            row=4, column=0, sticky="w", padx=10, pady=5
        )
        self.get_storage_details()
# •=====• Settings •=====•

    def create_settings(self): #creates the settings page

        self.settings = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color="transparent"
        )

        self.settings.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=30,
            pady=30
        )

        settings_title =ctk.CTkLabel(
            self.settings,
            text="Settings", #sets the title for thes settings page
            font=ctk.CTkFont(size=28, weight ="bold") #Sets the title as bold and makes it larger to stand out from other text
        )
        settings_title.grid(row=0, column=0, sticky="w")

        settings_subtitle = ctk.CTkLabel(
            self.settings,
            text="Basic settings and options" #subtitle
        )
        settings_subtitle.grid(row=1, column=0, sticky="w", pady=(5,20))

        #Appearance Options (Creates another section to the Settings page to contain options to change the app's customization)
        appearance_frame = ctk.CTkFrame(self.settings)

        appearance_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=10
        )

        appearance_title = ctk.CTkLabel(
        appearance_frame,
        text="Appearance", # Sets the subsection's title as "Appearance"
        font=ctk.CTkFont(size=20, weight="bold")
        )

        appearance_title.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        #Button colour changer
        button_colour = ctk.CTkButton(
        appearance_frame,
        text="Button Colour", # Sets the name of the button in its centre
        command=self.change_button_colour #Opens tkinter's colour picker to let the user choose a colour and return its hexadecimal value
        )

        button_colour.grid(
            row=1,
            column=0,
            padx=20,
            pady=10,
            sticky="w"
        )

        appearance_mode = ctk.CTkOptionMenu( #Creates a dropdown menu that present the appearance options to choose from when pressed
            appearance_frame,
            values=["Dark", "Light"], # lets the user choose from customtkinter's ligt/dark modes
            command=self.change_appearance_mode #Takes the user's input to change the background colour
        )

        appearance_mode.grid(
            row=2,
            column=0,
            padx=20,
            pady=10,
            sticky="w"
        )


    # •=====• Navigation •=====•

    def show_dashboard(self): #Opens the dashboard 
        print("Dashboard selected") #prints an indicator into the terminal
        self.hide_pages() #hides the page currently in use
        self.dashboard.grid( #opens the dashboard page
            row=0,
            column=1,
            sticky="nsew",
            padx=30,
            pady=30
        )

    def show_CPU(self): #Opens the CPU page
        print("CPU selected") #prints an indicator into terminal
        self.hide_pages() #Hides the other pages
        self.cpu_page.grid( #Shows the CPU page
            row=0,
            column=1,
            sticky="nsew",
            padx=30,
            pady=30
        )

    def show_memory(self): #Opens the memory page
        print("Memory selected") #prints an indicator into terminal
        self.hide_pages() #Hides the other pages
        self.memory_page.grid( #Shows the memory page
            row=0,
            column=1,
            sticky="nsew",
            padx=30,
            pady=30
        )

    def show_storage(self): #Opens the storage page
        print("Storage selected") #prints an indicator into terminal
        self.hide_pages() #Hides the other pages
        self.storage_page.grid( #Shows the storage page
            row=0,
            column=1,
            sticky="nsew",
            padx=30,
            pady=30
        )

    def show_settings(self): #opens the settings menu
            print("Settings selected") #prints an indicator into terminal
            self.hide_pages() #hides the page currently in use
            self.settings.grid( #Shows the settings page
                row=0,
                column=1,
                sticky="nsew",
                padx=30,
                pady=30
        )

    def hide_pages(self): #Function to hide the active page when switching to another
        self.dashboard.grid_forget()
        self.settings.grid_forget()
        self.cpu_page.grid_forget()
        self.memory_page.grid_forget()
        self.storage_page.grid_forget()

    # == Component info/database buttons ==
    
    #CPU
    def open_cpu_info(self):
        print("CPU information selected")
        webbrowser.open(
            "https://support.microsoft.com/en-gb/windows/experience/compatibility/all-about-processors-cpus"
        )
    #def open_cpu_database(self):
        #print("CPU upgrade database selected")

    #Memory
    def open_memory_info(self):
        print("Memory information selected")
        webbrowser.open(
            "https://support.microsoft.com/en-us/windows/experience/compatibility/all-about-computer-memory"
        )
    #def open_memory_database(self):
        #print("Memory upgrade database selected")

    #Storage
    def open_storage_info(self):
        print("Storage information selected")
        webbrowser.open(
            "https://support.microsoft.com/en-us/windows/experience/find-information-about-your-windows-device"
        )
    #def open_storage_database(self):
        #print("Storage upgrade database selected")

# •=====• Run application •=====•

if __name__ == "__main__":

    app = HardwareMonitor()

    app.mainloop() #Runs the application and keeps it running until the window is closed
