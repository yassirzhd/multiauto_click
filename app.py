import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pynput import mouse
import pyautogui
import time
import logging
import threading
import json
import logging
auto_detection_active = False

# Dictionary to store profiles with their settings
profiles = {i: {'text_field_x': None, 'text_field_y': None,
                'button_x': None, 'button_y': None,
                'boton_ferm_x': None, 'boton_ferm_y': None,
                'filename': None, 'log_filename': None,
                'wait_time': 60, 'additional_wait_time': 1,
                'is_running': False} for i in range(1, 9)}

# Track which profile is active
active_profile = 1

# Global variables for controlling the stopping of automation
stop_event = threading.Event()
profile_threads = {}
mouse_listener = None

# Function to handle mouse clicks and save coordinates
def on_click(x, y, button, pressed):
    global active_profile
    if pressed:
        print(f"Clicked at ({x}, {y}) for profile {active_profile}")  # Debugging output
        profile_data = profiles[active_profile]
        if profile_data['text_field_x'] is None:
            profile_data['text_field_x'] = x
            profile_data['text_field_y'] = y
            text_field_x_entries[active_profile].delete(0, tk.END)
            text_field_x_entries[active_profile].insert(0, str(x))
            text_field_y_entries[active_profile].delete(0, tk.END)
            text_field_y_entries[active_profile].insert(0, str(y))
        elif profile_data['button_x'] is None:
            profile_data['button_x'] = x
            profile_data['button_y'] = y
            button_x_entries[active_profile].delete(0, tk.END)
            button_x_entries[active_profile].insert(0, str(x))
            button_y_entries[active_profile].delete(0, tk.END)
            button_y_entries[active_profile].insert(0, str(y))
        elif profile_data['boton_ferm_x'] is None:
            profile_data['boton_ferm_x'] = x
            profile_data['boton_ferm_y'] = y
            boton_ferm_x_entries[active_profile].delete(0, tk.END)
            boton_ferm_x_entries[active_profile].insert(0, str(x))
            boton_ferm_y_entries[active_profile].delete(0, tk.END)
            boton_ferm_y_entries[active_profile].insert(0, str(y))
        if all([profile_data['text_field_x'], 
                profile_data['button_x'], 
                profile_data['boton_ferm_x']]):
            print(f"All coordinates set for profile {active_profile}")  # Debugging output
            mouse_listener.stop()




# Function to start mouse listener in a separate thread
def start_mouse_listener():
    global mouse_listener
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.start()
    

# Function to setup logging
def setup_logging(log_filename):
    logging.basicConfig(filename=log_filename,
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

# Function to read numbers from a file
def read_numbers_from_file(filename):
    with open(filename, 'r') as file:
        # Read lines from file and strip any extra whitespace/newlines
        numbers = [line.strip() for line in file if line.strip().isdigit()]
    return numbers

# Function to start the automation process for a single profile
def start_automation(profile):
    profile_data = profiles[profile]
    if not profile_data['filename'] or not profile_data['log_filename']:
        messagebox.showerror("Error", f"Please select both the numbers file and log file for Profile {profile}.")
        return
    if not all([profile_data['text_field_x'], 
                profile_data['button_x'], 
                profile_data['boton_ferm_x']]):
        messagebox.showerror("Error", f"Please set all coordinates for Profile {profile}.")
        return
    
    setup_logging(profile_data['log_filename'])
    numbers = read_numbers_from_file(profile_data['filename'])

    profile_data['is_running'] = True
    for number in numbers:
        if stop_event.is_set():
            break
        try:
            pyautogui.moveTo(profile_data['boton_ferm_x'], profile_data['boton_ferm_y'])
            pyautogui.click()
            time.sleep(profile_data['additional_wait_time'])

            pyautogui.moveTo(profile_data['text_field_x'], profile_data['text_field_y'])
            pyautogui.doubleClick()
            time.sleep(profile_data['additional_wait_time'])
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            time.sleep(profile_data['additional_wait_time'])
            pyautogui.typewrite(number)

            pyautogui.moveTo(profile_data['button_x'], profile_data['button_y'])
            pyautogui.doubleClick()
            time.sleep(profile_data['wait_time'])

            logging.info(f"Successfully processed number: {number}")
        except Exception as e:
            logging.error(f"An error occurred while processing number {number}: {e}")

    logging.info("Finished processing all numbers.")
    profile_data['is_running'] = False
    if not stop_event.is_set():
        messagebox.showinfo("Info", f"Finished processing all numbers for Profile {profile}.")

# Function to start automation for a profile in a new thread
def start_profile(profile):
    stop_event.clear()
    thread = threading.Thread(target=start_automation, args=(profile,))
    profile_threads[profile] = thread
    thread.start()

# Function to stop all profiles
def stop_all_profiles():
    stop_event.set()
    for profile, thread in profile_threads.items():
        if thread.is_alive():
            thread.join()  # Wait for the thread to stop
    messagebox.showinfo("Info", "All profiles have been stopped.")

# Function to start all profiles automatically
def start_all_profiles_automatically():
    try:
        wait_between_profiles = int(global_wait_time_entry.get())
        if wait_between_profiles <= 0:
            raise ValueError("Wait time must be positive.")
    except ValueError as e:
        messagebox.showerror("Error", f"Invalid wait time: {e}")
        return
    
    def run_profiles():
        for profile in range(1, 9):
            start_profile(profile)
            time.sleep(wait_between_profiles)
    
    threading.Thread(target=run_profiles).start()

# File selection functions
def select_numbers_file(profile):
    filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if filename:
        profiles[profile]['filename'] = filename
        numbers_file_labels[profile].config(text=f"Numbers file: {filename}")

def select_log_file(profile):
    log_filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
    if log_filename:
        profiles[profile]['log_filename'] = log_filename
        log_file_labels[profile].config(text=f"Log file: {log_filename}")

# Function to clear coordinates
def clear_coordinates(profile, field):
    if field == 'text_field':
        profiles[profile]['text_field_x'] = None
        profiles[profile]['text_field_y'] = None
        text_field_x_entries[profile].delete(0, tk.END)
        text_field_y_entries[profile].delete(0, tk.END)
    elif field == 'button':
        profiles[profile]['button_x'] = None
        profiles[profile]['button_y'] = None
        button_x_entries[profile].delete(0, tk.END)
        button_y_entries[profile].delete(0, tk.END)
    elif field == 'boton_ferm':
        profiles[profile]['boton_ferm_x'] = None
        profiles[profile]['boton_ferm_y'] = None
        boton_ferm_x_entries[profile].delete(0, tk.END)
        boton_ferm_y_entries[profile].delete(0, tk.END)

# Function to update wait times
def update_wait_times(profile):
    try:
        wait_time = int(wait_time_entries[profile].get())
        additional_wait_time = int(additional_wait_time_entries[profile].get())
        profiles[profile]['wait_time'] = wait_time
        profiles[profile]['additional_wait_time'] = additional_wait_time
    except ValueError:
        messagebox.showerror("Error", "Please enter valid integers for wait times.")

# Function to start auto-detection of coordinates
def start_auto_detection(profile):
    global mouse_listener, auto_detection_active, active_profile
    if auto_detection_active:
        messagebox.showwarning("Warning", "Auto-detection is already in progress.")
        return

    auto_detection_active = True
    active_profile = profile  # Set the active profile to the one being edited
    stop_event.clear()  # Ensure that stop_event is cleared so the listener can function

    def setup_and_run_listener():
        global mouse_listener
        mouse_listener = mouse.Listener(on_click=on_click)
        mouse_listener.start()
        mouse_listener.join()  # Wait for the listener to stop
        global auto_detection_active
        auto_detection_active = False  # Reset the flag when done

    threading.Thread(target=setup_and_run_listener).start()
    messagebox.showinfo("Info", f"Profile {profile}: Click on the desired locations. The auto-detection will stop after the required coordinates are set.")

# Function to save a single profile
def save_profile(profile):
    filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if filename:
        profile_data = profiles[profile]
        with open(filename, 'w') as file:
            json.dump(profile_data, file, indent=4)
        messagebox.showinfo("Info", f"Profile {profile} saved successfully.")

# Function to load a single profile
def load_profile(profile):
    filename = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if filename:
        with open(filename, 'r') as file:
            profile_data = json.load(file)
        profiles[profile].update(profile_data)
        update_profile_tab(profile)
        messagebox.showinfo("Info", f"Profile {profile} loaded successfully.")

# Function to save all profiles
def save_all_profiles():
    filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if filename:
        with open(filename, 'w') as file:
            json.dump(profiles, file, indent=4)
        messagebox.showinfo("Info", "All profiles saved successfully.")

# Function to load all profiles
def load_all_profiles():
    filename = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if filename:
        with open(filename, 'r') as file:
            all_profiles_data = json.load(file)
        global profiles
        profiles = all_profiles_data
        # Update each profile tab with the loaded data
        for profile in range(1, 9):
            update_profile_tab(profile)
        messagebox.showinfo("Info", "All profiles loaded successfully.")

# Function to update profile tab with new profile data
def update_profile_tab(profile):
    profile_data = profiles[profile]
    if profile_data['text_field_x'] is not None:
        text_field_x_entries[profile].delete(0, tk.END)
        text_field_x_entries[profile].insert(0, str(profile_data['text_field_x']))
    if profile_data['text_field_y'] is not None:
        text_field_y_entries[profile].delete(0, tk.END)
        text_field_y_entries[profile].insert(0, str(profile_data['text_field_y']))
    if profile_data['button_x'] is not None:
        button_x_entries[profile].delete(0, tk.END)
        button_x_entries[profile].insert(0, str(profile_data['button_x']))
    if profile_data['button_y'] is not None:
        button_y_entries[profile].delete(0, tk.END)
        button_y_entries[profile].insert(0, str(profile_data['button_y']))
    if profile_data['boton_ferm_x'] is not None:
        boton_ferm_x_entries[profile].delete(0, tk.END)
        boton_ferm_x_entries[profile].insert(0, str(profile_data['boton_ferm_x']))
    if profile_data['boton_ferm_y'] is not None:
        boton_ferm_y_entries[profile].delete(0, tk.END)
        boton_ferm_y_entries[profile].insert(0, str(profile_data['boton_ferm_y']))
    if profile_data['wait_time'] is not None:
        wait_time_entries[profile].delete(0, tk.END)
        wait_time_entries[profile].insert(0, str(profile_data['wait_time']))
    if profile_data['additional_wait_time'] is not None:
        additional_wait_time_entries[profile].delete(0, tk.END)
        additional_wait_time_entries[profile].insert(0, str(profile_data['additional_wait_time']))

# Create the GUI window
root = tk.Tk()
root.title("Automation Setup")
root.geometry("800x600")  # Adjusted for additional elements

# Create a Notebook for tabbed profiles and main page
notebook = ttk.Notebook(root)
notebook.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

# Function to stop automation for a specific profile
def stop_profile(profile):
    stop_event.set()
    if profile in profile_threads and profile_threads[profile].is_alive():
        stop_event.set()  # Trigger the stop event to stop automation
        profile_threads[profile].join()  # Wait for the thread to finish
        messagebox.showinfo("Info", f"Profile {profile} has been stopped.")

# Modify the create_profile_tab function to include a stop button
def create_profile_tab(tab_name, profile):
    frame = tk.Frame(notebook)
    notebook.add(frame, text=tab_name)
    
    # Create Canvas and Scrollbar
    canvas = tk.Canvas(frame)
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    # Create a window inside the canvas
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Pack scrollbar and canvas into the frame
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    scrollable_frame.update_idletasks()

    # Update the scroll region of the canvas
    canvas.config(scrollregion=canvas.bbox("all"))

    # Create frames inside the scrollable_frame
    file_frame = tk.Frame(scrollable_frame)
    file_frame.grid(row=0, column=0, pady=10, padx=10, sticky="ew")

    coords_frame = tk.Frame(scrollable_frame)
    coords_frame.grid(row=1, column=0, pady=10, padx=10, sticky="ew")

    settings_frame = tk.Frame(scrollable_frame)
    settings_frame.grid(row=2, column=0, pady=10, padx=10, sticky="ew")

    actions_frame = tk.Frame(scrollable_frame)
    actions_frame.grid(row=3, column=0, pady=10, padx=10, sticky="ew")

    # File Selection Widgets
    tk.Label(file_frame, text="File Settings", font=('Arial', 14, 'bold')).pack(pady=5)
    tk.Button(file_frame, text="Select Numbers File", command=lambda: select_numbers_file(profile)).pack(pady=5)
    tk.Button(file_frame, text="Select Log File", command=lambda: select_log_file(profile)).pack(pady=5)
    
    numbers_file_labels[profile] = tk.Label(file_frame, text="Numbers file: Not selected")
    numbers_file_labels[profile].pack(pady=5)
    
    log_file_labels[profile] = tk.Label(file_frame, text="Log file: Not selected")
    log_file_labels[profile].pack(pady=5)

    # Coordinate Entry Widgets
    tk.Label(coords_frame, text="Coordinates", font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=5, pady=5)
    
    tk.Label(coords_frame, text="Text Field X:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
    text_field_x_entries[profile] = tk.Entry(coords_frame, width=10)
    text_field_x_entries[profile].grid(row=1, column=1, padx=5, pady=5)
    
    tk.Label(coords_frame, text="Text Field Y:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
    text_field_y_entries[profile] = tk.Entry(coords_frame, width=10)
    text_field_y_entries[profile].grid(row=1, column=3, padx=5, pady=5)
    
    tk.Button(coords_frame, text="Clear", command=lambda: clear_coordinates(profile, 'text_field')).grid(row=1, column=4, padx=5, pady=5)
    
    tk.Label(coords_frame, text="Button X:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
    button_x_entries[profile] = tk.Entry(coords_frame, width=10)
    button_x_entries[profile].grid(row=2, column=1, padx=5, pady=5)
    
    tk.Label(coords_frame, text="Button Y:").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
    button_y_entries[profile] = tk.Entry(coords_frame, width=10)
    button_y_entries[profile].grid(row=2, column=3, padx=5, pady=5)
    
    tk.Button(coords_frame, text="Clear", command=lambda: clear_coordinates(profile, 'button')).grid(row=2, column=4, padx=5, pady=5)
    
    tk.Label(coords_frame, text="Boton Ferm X:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
    boton_ferm_x_entries[profile] = tk.Entry(coords_frame, width=10)
    boton_ferm_x_entries[profile].grid(row=3, column=1, padx=5, pady=5)
    
    tk.Label(coords_frame, text="Boton Ferm Y:").grid(row=3, column=2, padx=5, pady=5, sticky=tk.W)
    boton_ferm_y_entries[profile] = tk.Entry(coords_frame, width=10)
    boton_ferm_y_entries[profile].grid(row=3, column=3, padx=5, pady=5)
    
    tk.Button(coords_frame, text="Clear", command=lambda: clear_coordinates(profile, 'boton_ferm')).grid(row=3, column=4, padx=5, pady=5)

    # Settings Frame
    tk.Label(settings_frame, text="Automation Settings", font=('Arial', 14, 'bold')).pack(pady=5)
    tk.Label(settings_frame, text="Wait Time (seconds):").pack(pady=5)
    wait_time_entry = tk.Entry(settings_frame)
    wait_time_entry.pack(pady=5)
    wait_time_entry.insert(0, str(profiles[profile]['wait_time']))
    wait_time_entries[profile] = wait_time_entry
    tk.Label(settings_frame, text="Additional Wait Time (seconds):").pack(pady=5)
    additional_wait_time_entry = tk.Entry(settings_frame)
    additional_wait_time_entry.pack(pady=5)
    additional_wait_time_entry.insert(0, str(profiles[profile]['additional_wait_time']))
    additional_wait_time_entries[profile] = additional_wait_time_entry
    tk.Button(settings_frame, text="Update Wait Times", command=lambda: update_wait_times(profile)).pack(pady=10)

    # Actions Frame
    tk.Button(actions_frame, text="Start Automation", command=lambda: start_profile(profile), bg="blue", fg="white").pack(pady=20)
    tk.Button(actions_frame, text="Stop Automation", command=lambda: stop_profile(profile), bg="red", fg="white").pack(pady=20)
    tk.Button(actions_frame, text="Start Auto-Detection", command=lambda: start_auto_detection(profile), bg="green", fg="white").pack(pady=20)
    tk.Button(actions_frame, text="Save Profile", command=lambda: save_profile(profile), bg="purple", fg="white").pack(pady=5)
    tk.Button(actions_frame, text="Load Profile", command=lambda: load_profile(profile), bg="orange", fg="white").pack(pady=5)

    # Update scroll region
    scrollable_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

# Create the main page tab
main_page_frame = tk.Frame(notebook)
notebook.add(main_page_frame, text="Main Page")

# Main Page Widgets
tk.Label(main_page_frame, text="Main Controls", font=('Arial', 14, 'bold')).pack(pady=10)

# Existing Main Control Buttons
tk.Button(main_page_frame, text="Start All Profiles Automatically", command=start_all_profiles_automatically, bg="blue", fg="white").pack(pady=10)
tk.Button(main_page_frame, text="Stop All Profiles", command=stop_all_profiles, bg="red", fg="white").pack(pady=10)
tk.Button(main_page_frame, text="Save All Profiles", command=save_all_profiles, bg="purple", fg="white").pack(pady=10)
tk.Button(main_page_frame, text="Load All Profiles", command=load_all_profiles, bg="orange", fg="white").pack(pady=10)

# Wait Time Between Profiles Entry
tk.Label(main_page_frame, text="Wait Time Between Profiles (seconds):").pack(pady=5)
global_wait_time_entry = tk.Entry(main_page_frame)
global_wait_time_entry.pack(pady=5)

# Buttons to Start Each Profile
tk.Label(main_page_frame, text="Start Profiles", font=('Arial', 14, 'bold')).pack(pady=10)
profile_buttons_frame = tk.Frame(main_page_frame)
profile_buttons_frame.pack(pady=10)

for i in range(1, 9):
    tk.Button(profile_buttons_frame, text=f"Start Profile {i}", command=lambda p=i: start_profile(p), bg="blue", fg="white").pack(pady=5)

# Create profile tabs
text_field_x_entries = {}
text_field_y_entries = {}
button_x_entries = {}
button_y_entries = {}
boton_ferm_x_entries = {}
boton_ferm_y_entries = {}
wait_time_entries = {}
additional_wait_time_entries = {}
numbers_file_labels = {}
log_file_labels = {}

for i in range(1, 9):
    create_profile_tab(f"Profile {i}", i)

root.mainloop()
