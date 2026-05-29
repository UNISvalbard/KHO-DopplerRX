"""
Visual tool for converting the files, creating spectrograms, and plotting them.

Code taken from the SuperDARN visual tool and modified to fit the needs for this project

Requires spectrogram_netcdf.py and netcdf-metadata.py to be in the same folder
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import datetime as dt
import numpy as np
import xarray as xr
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.widgets import Slider
import re
import subprocess
import sys
import threading
import configparser


class PRIDE_GUI() :
    def __init__(self, root) :
        # Meta variables
        self.root = root
        self.root.title("PRIDE visual tool")
        self.root.geometry("1600x900")

        # Define variables
        config = configparser.ConfigParser()
        config.read("config.ini")
        self.raw_dir = tk.StringVar(value=config['visual_tool_settings']['raw_data_folder'])
        self.publishable_dir = tk.StringVar(value=config['visual_tool_settings']['netcdf_folder'])
        self.spectrogram_dir = tk.StringVar(value=config['visual_tool_settings']['spectrogram_folder'])
        self.start_date = tk.StringVar(value="14/12/2023")
        self.end_date = tk.StringVar(value="31/12/2023")

        # Define layout
        self.create_navigation()
        self.create_container()
        self.create_converter_frame()
        self.create_plotter_frame()

    
    # ------------------------------------------------
    # Navigation tools functions
    def create_navigation(self) :
        """Creates the necessary buttons for switching from converting to plotting and vice-versa"""
        nav_frame = ttk.Frame(self.root)
        nav_frame.pack(fill="x", pady=10)
        ttk.Button(nav_frame, text="File converter tool", command=lambda: self.show_frame("converter")).pack(side="left", padx=10)
        ttk.Button(nav_frame, text="Plotter tool", command=lambda: self.show_frame("plotter")).pack(side="left")
    
    def create_container(self) :
        """Creates a space for the tools to appear in"""
        self.container = ttk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

    def show_frame(self, frame_name) :
        self.converter_frame.pack_forget()
        self.plotter_frame.pack_forget()
        if frame_name == "converter":
            self.converter_frame.pack(fill="both", expand=True)
        elif frame_name == "plotter":
            self.plotter_frame.pack(fill="both", expand=True)
    

    # ------------------------------------------------
    # Converter functions
    def create_converter_frame(self) :
        self.converter_frame = ttk.Frame(self.container)
        title = ttk.Label(self.converter_frame, text="File Converter", font=("Arial", 18))
        title.pack(pady=20)

        # Directory selector
        self.create_directory_selector(parent=self.converter_frame, label="Raw files Directory", variable=self.raw_dir)
        self.create_directory_selector(parent=self.converter_frame, label="Publishable netcdf files Directory", variable=self.publishable_dir)
        self.create_directory_selector(parent=self.converter_frame, label="Spectrogram timeseries Directory", variable=self.spectrogram_dir)

        # Dates selector
        dates_frame = ttk.Frame(self.converter_frame)
        dates_frame.pack(fill="x", padx=20, pady=15)
        ttk.Label(dates_frame, text="Start Date:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(dates_frame, textvariable=self.start_date, width=20).grid(row=0, column=1, padx=5)
        ttk.Label(dates_frame, text="DD/MM/YYYY format").grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(dates_frame, text="End Date:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(dates_frame, textvariable=self.end_date, width=20).grid(row=1, column=1, padx=5)
        ttk.Label(dates_frame, text="DD/MM/YYYY format").grid(row=1, column=2, padx=5, pady=5)

        # Convert button
        button_frame = ttk.Frame(self.converter_frame)
        button_frame.pack(pady=20)
        self.create_publishable_button = ttk.Button(button_frame, text="Create publishable Files", command=self.create_publishable_files, width=20)
        self.create_publishable_button.pack(side="left", padx=10)
        self.create_timeseries_button = ttk.Button(button_frame, text="Create spectrogram Files", command=self.create_timeseries_files, width=20)
        self.create_timeseries_button.pack(side="left", padx=10)

        # Conversion status
        self.conversion_status = ttk.Label(self.converter_frame, text="")
        self.conversion_status.pack(pady=10)
    
    def create_publishable_files(self) :
        """
        Creates netcdf files with metadata from raw data from the Doppler Radar.
        All the data recorder between the given start_date and end_date will be converted using the netcdf-metadata.py script.
        """
        try :
            self.create_publishable_button.config(state="disabled")

            # Retreive the given dates and directories
            raw_start_date = self.start_date.get()
            raw_end_date = self.end_date.get()
            start_date = dt.datetime.strptime(re.sub(r'[-./]', '/', raw_start_date), "%d/%m/%Y").date()
            end_date = dt.datetime.strptime(re.sub(r'[-./]', '/', raw_end_date), "%d/%m/%Y").date()

            origin_dir = self.raw_dir.get()
            destination_dir = self.publishable_dir.get()

            if not Path(origin_dir).exists() :
                raise Exception("Invalid raw files directory")
            if not Path(destination_dir).exists() :
                raise Exception("Invalid publishable files directory")

            # Start conversion
            self.conversion_status.config(text="Conversion running...")
            self.root.update_idletasks()
            threading.Thread(target=self.conversion_worker, args=(start_date, end_date, 'publishable'), daemon=True).start()

        except Exception as err :
            self.conversion_status.config(text="Conversion failed")
            messagebox.showerror("Error: ", str(err))
        
        finally :
            self.create_publishable_button.config(state="normal")

    def create_timeseries_files(self) :
        """
        Creates timeseries files in netcdf format with the publishable netcdf data from the Doppler Radar.
        All the data recorder between the given start_date and end_date will be converted using the spectrogram_netcdf.py script.
        """
        try :
            self.create_timeseries_button.config(state="disabled")

            # Retreive the given dates and directories
            raw_start_date = self.start_date.get()
            raw_end_date = self.end_date.get()
            start_date = dt.datetime.strptime(re.sub(r'[-./]', '/', raw_start_date), "%d/%m/%Y").date()
            end_date = dt.datetime.strptime(re.sub(r'[-./]', '/', raw_end_date), "%d/%m/%Y").date()

            origin_dir = self.publishable_dir.get()
            destination_dir = self.spectrogram_dir.get()

            if not Path(origin_dir).exists() :
                raise Exception("Invalid publishable files directory")
            if not Path(destination_dir).exists() :
                raise Exception("Invalid spectrogram files directory")

            # Start conversion
            self.conversion_status.config(text="Conversion running...")
            self.root.update_idletasks()
            threading.Thread(target=self.conversion_worker, args=(start_date, end_date, 'spectrogram'), daemon=True).start()

        except Exception as err :
            self.conversion_status.config(text="Conversion failed")
            messagebox.showerror("Error: ", str(err))
        
        finally :
            self.create_timeseries_button.config(state="normal")
    
    def conversion_worker(self, start_date, end_date, mode) :
        try : 
            working_date = start_date
            nbr_files_converted = 0
            if mode == 'publishable':
                script = 'netcdf-metadata.py'
            elif mode == 'spectrogram':
                script = 'spectrogram_netcdf.py'
            while working_date <= end_date :
                try :
                    # create one publishable file
                    subprocess.run([sys.executable, script, f'-d={working_date.strftime('%Y/%m/%d')}'], check=True)
                    nbr_files_converted += 1
                    self.conversion_status.config(text=f'Conversion running... {nbr_files_converted} {mode} files created.')
                except FileNotFoundError as err :
                    self.conversion_status.config(text=f'Conversion running... {nbr_files_converted} {mode} files created. No file found for {working_date.strftime('%Y/%m/%d')}')
                finally :
                    working_date += dt.timedelta(days=1)
            self.conversion_status.config(text=f'Conversion completed. {nbr_files_converted} {mode} files created.')
        except Exception as err :
            self.conversion_status.config(text="Conversion failed")
            messagebox.showerror("Error: ", str(err))
        finally :
            self.create_timeseries_button.config(state="normal")

    
    # ------------------------------------------------
    # Plotting function
    def create_plotter_frame(self) :
        self.plotter_frame = ttk.Frame(self.container)
        title = ttk.Label(self.plotter_frame, text="Plotter", font=("Arial", 18))
        title.pack(pady=15)

        # Directory selector
        self.create_directory_selector(parent=self.plotter_frame, label="Spectrogram timeseries Directory", variable=self.spectrogram_dir)

        # Parameters 
        self.parameters_frame = ttk.Frame(self.plotter_frame)
        self.parameters_frame.pack(fill='x', padx=20, pady=5)

        # # Plotting mode selector
        # mode_frame = ttk.LabelFrame(self.parameters_frame, text="Plotting Mode")
        # mode_frame.grid(row=0, column=1, padx=20, pady=5)
        # ttk.Radiobutton(mode_frame, text="Full Day", variable=self.plot_time, value="full_day").grid(row=0, column=0, padx=5, pady=5)
        # ttk.Radiobutton(mode_frame, text="File By File", variable=self.plot_time, value="file_by_file").grid(row=0, column=1, padx=5, pady=5)

        # ttk.Radiobutton(mode_frame, text="Summary", variable=self.plot_type, value="summary").grid(row=1, column=0, padx=5, pady=5)
        # ttk.Radiobutton(mode_frame, text="Line of sight velocity", variable=self.plot_type, value="v").grid(row=1, column=1, padx=5, pady=5)
        # ttk.Radiobutton(mode_frame, text="SNR", variable=self.plot_type, value="p_l").grid(row=1, column=2, padx=5, pady=5)
        # ttk.Radiobutton(mode_frame, text="Spectral width", variable=self.plot_type, value="w_l").grid(row=1, column=3, padx=5, pady=5)
        # ttk.Radiobutton(mode_frame, text="Elevation angle", variable=self.plot_type, value="elv").grid(row=1, column=4, padx=5, pady=5)
        
        # Dates selector
        dates_frame = ttk.Frame(self.parameters_frame)
        dates_frame.grid(row=0, column=0, padx=20, pady=5)
        ttk.Label(dates_frame, text="Start Date:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(dates_frame, textvariable=self.start_date, width=20).grid(row=0, column=1, padx=5)
        ttk.Label(dates_frame, text="DD/MM/YYYY format").grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Separator(dates_frame, orient='horizontal').grid(row=0, column=3, padx=15)
        ttk.Button(dates_frame, text="Previous day", command=lambda : self.update_start_date(dt.timedelta(days=-1))).grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(dates_frame, text="Next day", command=lambda : self.update_start_date(dt.timedelta(days=1))).grid(row=0, column=5, padx=5, pady=5)
        
        # Plotting button
        ttk.Separator(dates_frame, orient='horizontal').grid(row=0, column=6, padx=15)
        self.plot_button = ttk.Button(dates_frame, text="Generate Plot", command=self.display_plot)
        self.plot_button.grid(row=0, column=7, padx=5, pady=5)
        
        # Plotting area
        self.plot_canvas_frame = ttk.Frame(self.plotter_frame)
        self.plot_canvas_frame.pack(fill="both", expand=True, padx=20, pady=5)
    
    def update_start_date(self, time_delta) :
        date = dt.datetime.strptime(self.start_date.get(), '%d/%m/%Y')
        date += time_delta
        self.start_date.set(date.strftime('%d/%m/%Y'))

    def display_plot(self) :
        try :
            self.plot_button.config(state="disabled")

            # Remove previous plot
            for widget in self.plot_canvas_frame.winfo_children():
                widget.destroy()

            # Get parameters
            spectrogram_dir = self.spectrogram_dir.get()
            if not Path(spectrogram_dir).exists() :
                raise Exception("Invalid fit files directory")

            raw_start_date = self.start_date.get()
            start_date = dt.datetime.strptime(re.sub(r'[-./]', '/', raw_start_date), "%d/%m/%Y")

            # Read the data
            data_dict, plot_date = read_spectrogram_file(Path(spectrogram_dir), start_date)
            # ttk.Label(self.plot_canvas_frame, text="No data for given date")
            
            # Display the plot
            fig, ax = create_spectrogram_plot(data_dict, plot_date)

            canvas = FigureCanvasTkAgg(fig, master=self.plot_canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        except Exception as err :
            messagebox.showerror("Error: ", str(err))

        finally :
            self.plot_button.config(state="normal")

    # ------------------------------------------------
    # General purpose functions
    def create_directory_selector(self, parent, label, variable) :
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=20, pady=5)
        ttk.Label(frame, text=label).pack(anchor="w")

        subframe = ttk.Frame(frame)
        subframe.pack(fill="x", pady=5)
        ttk.Entry(subframe, textvariable=variable).pack(side="left", fill="x", expand=True)

        ttk.Button(subframe, text="Browse", command=lambda: self.select_directory(variable)).pack(side="left", padx=5)

    def select_directory(self, variable) :
        """Function for selecting source and target directories"""
        dir = filedialog.askdirectory()
        if dir :
            variable.set(dir)


# ------------------------------------------------
# Reading and plotting functions

def read_spectrogram_file(spectrogram_dir:Path, date:dt.datetime) :
    time_series_file = spectrogram_dir / f'test_PRIDE_spectrogram_{date.strftime('%Y%m%d')}.nc'
    with xr.open_dataset(time_series_file, decode_cf=False) as timeseries_dataset :

        data_dict = {}
        data_dict['time'] = np.array(timeseries_dataset['time'])
        data_dict['max_freq'] = np.array(timeseries_dataset['max_freq'])

        plot_date_str = timeseries_dataset['time'].attrs['units'].split(' ')[2]
        plot_date = dt.datetime.fromisoformat(plot_date_str)
        data_dict['timestamps'] = np.array([plot_date + dt.timedelta(seconds=int(data_dict['time'][k])) for k in range(len(data_dict['time']))])
    
    return data_dict, plot_date

def create_spectrogram_plot(data_dict, plot_date) :
    # Avoid using matplotlib.pyplot as it prevents tkinter window from closing
    fig = Figure(figsize=(18, 5))
    ax = fig.add_subplot()
    fig.subplots_adjust(bottom=0.2)

    x_data = data_dict['timestamps']

    ax.plot(x_data, data_dict['max_freq'], linestyle='None', marker='+', markersize=4)
    ax.set_xlim(x_data[0], x_data[-1])
    ax.set_autoscale_on(False)

    ax.set_title(f"Frequency of Strongest Peak vs Time - filtered and downshifted - {plot_date.strftime('%Y/%m/%d')}")
    ax.set_xlabel("Time")
    ax.set_ylabel("Frequency of Maximum PSD (Hz)")
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))


    # Slider definition and fig update 
    window_width = dt.timedelta(hours=1)
    ax_slider = fig.add_axes(rect=(0.1, 0.05, 0.8, 0.03))
    slider = Slider(ax=ax_slider, label="Displayed hour", valmin=0, valmax=1, valinit=0)

    def format_time(val) : 
        return x_data[0] + val * (x_data[-1] - dt.timedelta(hours=1) - x_data[0])

    slider.valtext.set_text(f"{format_time(slider.val).strftime('%H:%M')}")

    def update(val) :
        displayed_hour = format_time(slider.val)
        ax.set_xlim(displayed_hour, displayed_hour + window_width)
        slider.valtext.set_text(f"{displayed_hour.strftime('%H:%M')}")
    slider.on_changed(update)

    # Handling function for the mouse wheel
    def on_scroll(event) :
        if event.inaxes == ax_slider or event.inaxes == ax :
            current_val = slider.val
            step = 0.005
            
            if event.step < 0:
                new_val = min(current_val + step, slider.valmax)
            else:
                new_val = max(current_val - step, slider.valmin)
                
            slider.set_val(new_val)
    fig.canvas.mpl_connect('scroll_event', on_scroll)

    return fig, ax


# ------------------------------------------------
# Making script executable
if __name__ == "__main__" :
    root = tk.Tk()
    app = PRIDE_GUI(root)
    root.mainloop()