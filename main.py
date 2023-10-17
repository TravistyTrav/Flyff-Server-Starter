import tkinter
import tkinter.messagebox
from tkinter import filedialog
import subprocess
import os
import customtkinter
import pickle
import time
import win32gui
import win32con
import webbrowser
from config import server_info
from image_constants import (
    flyff_logo_star,
    github_logo,
    options_icon,
    offline,
    online,
    start_icon,
    stop_icon,
    edit_icon,
    feedback_icon
)

# Define the data file name
DATA_FILE = "server_manager_data.pkl"
DIR_FILE = "server_manager_dir_data.pkl"

customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

class settings_window(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("800x600")
        self.title("Server Manager - Configuration")

        self.entries = []  # Store Entry widgets in a list
        self.load_data()  # Load saved data when the application starts

        for server_key, server in enumerate(server_info):
            title_label = customtkinter.CTkLabel(self, text=f"Select {server['title']} file:", font=customtkinter.CTkFont(size=14))
            title_label.grid(row=server['row_start'], column=0, padx=20, pady=(5 if server['row_start'] == 0 else 0), sticky="w")

            entry = customtkinter.CTkEntry(self, placeholder_text="Select file...")
            entry.grid(row=server['row_start'] + 1, column=0, padx=(20, 5), pady=(5, 10), sticky='w')
            self.entries.append(entry)

            # If there is saved data for this server, populate the entry
            if server_key in self.data:
                entry.insert(0, self.data[server_key])

            button = customtkinter.CTkButton(self, text="Select", command=lambda e=entry, s=server_key: self.select_exe_file(e, s))
            button.grid(row=server['row_start'] + 1, column=1, padx=(0, 20), pady=(5, 10))

        save_exe_inputs = customtkinter.CTkButton(self, text="Clear Inputs", command=self.clear_data, fg_color="#CF352E", hover_color="#AD221C")
        save_exe_inputs.grid(row=14, column=0, padx=(20, 20), pady=(30, 20), sticky='w')

        save_exe_inputs = customtkinter.CTkButton(self, text="Save Inputs", command=self.save_data, fg_color="#429942", hover_color="#338233")
        save_exe_inputs.grid(row=14, column=1, padx=(5, 20), pady=(30, 20), sticky='w')

        status_label = customtkinter.CTkLabel(self, text="Select path to Server Files", anchor="e")
        status_label.grid(row=0, column=2, padx=20, pady=(10, 0), sticky="w")

        merge_compiles_source_input = customtkinter.CTkEntry(self, placeholder_text="Path to Server Files...")
        merge_compiles_source_input.grid(row=1, column=2, padx=20, pady=5, sticky="we")
        self.merge_compiles_source_input = merge_compiles_source_input

        select_source_location = customtkinter.CTkButton(self, text="Select")
        select_source_location.grid(row=1, column=3, padx=(5, 20), pady=5, sticky='w')


    # Define select_exe_file as a method of the class
    def select_exe_file(self, entry, server_key):
        file_path = filedialog.askopenfilename(filetypes=[("Executable Files", "*.exe")])
        if file_path:
            entry.delete(0, "end")
            entry.insert(0, file_path)
            self.data[server_key] = file_path  # Save the data when the user selects a file
            self.save_data()

    def save_data(self):
        with open(DATA_FILE, 'wb') as file:
            pickle.dump(self.data, file)

    def load_data(self):
        try:
            with open(DATA_FILE, 'rb') as file:
                self.data = pickle.load(file)
        except FileNotFoundError:
            self.data = {}  # Default empty data
    
    def clear_data(self):
        self.data = {}  # Clear the data dictionary
        for entry in self.entries:
            entry.delete(0, "end")  # Clear all Entry widgets
        self.save_data()  # Save the cleared data


    
class server_status(customtkinter.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app

        # Create a list to store status labels
        self.status_labels = []

        for row, server in enumerate(server_info, start=1):
            server_title = customtkinter.CTkLabel(self, text=f"{row}. {server['title']}", font=customtkinter.CTkFont(size=14), anchor="w")
            server_title.grid(row=row, column=0, padx=20, pady=10, sticky="w")
            
            status_label = customtkinter.CTkLabel(self, image=offline, text="", anchor="e")
            status_label.grid(row=row, column=1, padx=20, pady=10, sticky="e")

            # Add the status label to the list
            self.status_labels.append(status_label)


        start_server_button = customtkinter.CTkButton(self, text="Start Server", image=start_icon, command=self.app.start_servers)
        start_server_button.grid(row=row + 1, column=0, padx=20, pady=(20, 10), sticky="ew", columnspan=2)

        stop_server_button = customtkinter.CTkButton(self, text="Stop Server", fg_color="#CF352E", hover_color="#AD221C", image=stop_icon, command=self.app.stop_servers)
        stop_server_button.grid(row=row + 2, column=0, padx=20, pady=(10, 20), sticky="ew", columnspan=2)

    def start_servers_button_click(self):
        # Call the start_servers method of the App class
        self.app.start_servers()

    def stop_servers_button_click(self):
        # Call the start_servers method of the App class
        self.app.stop_servers()


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.subprocesses = []  # List to keep track of subprocesses

        # configure window
        self.title("Server Manager - by Amazic")
        self.geometry('440x580')

        # configure grid layout (2x4)
        self.grid_columnconfigure((1), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_image = customtkinter.CTkLabel(self.sidebar_frame, image=flyff_logo_star, text="")
        self.logo_image.grid(row=0, column=0, padx=0, pady=(20, 10))
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Server Manager", font=customtkinter.CTkFont(size=18, weight="bold"))
        self.logo_label.grid(row=1, column=0, padx=20, pady=(0, 10))
        self.string_input_button = customtkinter.CTkButton(self.sidebar_frame, image=github_logo, text="Github",
                                                           command=self.open_github)
        self.string_input_button.grid(row=2, column=0, padx=20, pady=(10, 10))
        self.merge_compile_button = customtkinter.CTkButton(self.sidebar_frame, text="Merge Compiles", image=edit_icon,
                                                           command=self.open_input_dialog_event)
        self.merge_compile_button.grid(row=7, column=0, padx=20, pady=(10, 10))
        self.string_input_button = customtkinter.CTkButton(self.sidebar_frame, image=options_icon, text="Configure",
                                                           command=self.open_settingswindow)
        self.string_input_button.grid(row=8, column=0, padx=20, pady=(10, 20))
        self.settings_window = None

        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=9, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=10, column=0, padx=20, pady=(10, 20))

        # Server Status Frame
        self.server_status_frame = server_status(master=self, app=self)
        self.server_status_frame.grid(row=0, column=1, padx=20, pady=(50, 20), sticky="ns")

        # Create the server_status_frame
        self.server_status_frame = server_status(master=self, app=self)
        self.server_status_frame.grid(row=0, column=1, padx=20, pady=(50, 20), sticky="ns")


        # Schedule the initial update and status check
        self.after(1000, self.update_server_status)


    def sidebar_button_event(self):
        print("sidebar_button click")
    
    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def open_input_dialog_event(self):
        dialog = customtkinter.CTkInputDialog(text="Type in a number:", title="CTkInputDialog")
        print("CTkInputDialog:", dialog.get_input())

    def load_data(self):
        try:
            with open(DATA_FILE, 'rb') as file:
                self.data = pickle.load(file)
        except FileNotFoundError:
            self.data = {}  # Default empty data

    def open_settingswindow(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = settings_window(self)  # create window if its None or destroyed  
        else:
            self.settings_window.focus()  # if window exists focus it

    def start_servers(self):
        self.load_data()  # Load saved data

        for server_key, exe_path in self.data.items():
            if os.path.isfile(exe_path):
                try:
                    # Execute the executable and append the subprocess to the list
                    process = subprocess.Popen(exe_path, cwd=os.path.dirname(exe_path))
                    self.subprocesses.append(process)

                    # Introduce a 1-second delay (adjust as needed)
                    time.sleep(1)

                    # Minimize the application window
                    hwnd = win32gui.GetForegroundWindow()
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)

                except Exception as e:
                    print(f"Error running executable for server {server_key}: {e}")
            else:
                print(f"Executable file not found for server {server_key}")


    def stop_servers(self):
        subprocesses_copy = self.subprocesses.copy()
        subprocesses_copy.reverse()  # Reverse the list
        for process in subprocesses_copy:
            try:
                process.terminate()  # Terminate each subprocess
                time.sleep(0.2)  # Add a 0.2s delay
                self.subprocesses.remove(process)  # Remove the terminated process from the list
            except Exception as e:
                print(f"Error terminating subprocess: {e}")


    def update_server_status(self):
        for server_key, status_label in enumerate(self.server_status_frame.status_labels):
            if server_key < len(self.subprocesses) and self.subprocesses[server_key].poll() is None:
                # Process is still running, set the status label to "Online"
                status_label.configure(image=online)
            else:
                # Process has exited, set the status label to "Offline"
                status_label.configure(image=offline)
    
        # Schedule the next update
        self.after(1000, self.update_server_status)

    def open_github(self):
        url = "https://github.com/TravistyTrav/Flyff-Server-Starter"
        webbrowser.open(url)
    

if __name__ == "__main__":
    app = App()
    app.mainloop()