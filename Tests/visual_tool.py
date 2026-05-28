"""
Visual tool for converting the files, creating spectrograms, and plotting them.

Code taken from the SuperDARN visual tool and modified to fit the needs for this project
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import datetime as dt
import re
import subprocess
import sys
import threading
import configparser
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


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
        self.specrogram_dir = tk.StringVar(value=config['visual_tool_settings']['spectrogram_folder'])
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
        self.create_directory_selector(parent=self.converter_frame, label="Spectrogram timeseries Directory", variable=self.specrogram_dir)

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
            destination_dir = self.specrogram_dir.get()

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
        self.create_directory_selector(parent=self.plotter_frame, label="Data Directory", variable=self.specrogram_dir)

        # Parameters 
        self.parameters_frame = ttk.Frame(self.plotter_frame)
        self.parameters_frame.pack(fill='x', padx=20, pady=5)

        # Dates selector
        dates_frame = ttk.Frame(self.parameters_frame)
        dates_frame.grid(row=0, column=0, padx=20, pady=5)
        ttk.Label(dates_frame, text="Start Date:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(dates_frame, textvariable=self.start_date, width=20).grid(row=0, column=1, padx=5)
        ttk.Label(dates_frame, text="DD/MM/YYYY format").grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Separator(dates_frame, orient='horizontal').grid(row=0, column=3, padx=15)
        ttk.Label(dates_frame, text="End Date:").grid(row=0, column=4, padx=5, pady=5)
        ttk.Entry(dates_frame, textvariable=self.end_date, width=20).grid(row=0, column=5, padx=5)
        ttk.Label(dates_frame, text="DD/MM/YYYY format").grid(row=0, column=6, padx=5, pady=5)

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

        # Plotting button
        self.plot_button = ttk.Button(self.plotter_frame, text="Generate Plot", command=self.display_plot)
        self.plot_button.pack(pady=5)
        
        # Plotting area
        self.plot_canvas_frame = ttk.Frame(self.plotter_frame)
        self.plot_canvas_frame.pack(fill="both", expand=True, padx=20, pady=5)

    # def display_plot(self) :
    #     try :
    #         self.plot_button.config(state="disabled")

    #         # Remove previous plot
    #         for widget in self.plot_canvas_frame.winfo_children():
    #             widget.destroy()
    #         plt.clf()

    #         # Get parameters
    #         plot_dir = self.fit_dir.get()
    #         if not Path(plot_dir).exists() :
    #             raise Exception("Invalid fit files directory")

    #         raw_start_date = self.start_date.get()
    #         raw_end_date = self.end_date.get()
    #         start_date = dt.datetime.strptime(re.sub(r'[-./]', '/', raw_start_date), "%d/%m/%Y").date()
    #         end_date = dt.datetime.strptime(re.sub(r'[-./]', '/', raw_end_date), "%d/%m/%Y").date()

    #         plot_time = self.plot_time.get()
    #         plot_type = self.plot_type.get()

    #         # Read the data
    #         if plot_time == "full_day" :
    #             fitacf_data = read_fitacf3_entire_day(Path(plot_dir), start_date)
    #         elif plot_time == "file_by_file" :
    #             fitacf_list = list_fitacf3_files(Path(plot_dir), start_date)
    #             if not fitacf_list :
    #                 ttk.Label(self.plot_canvas_frame, text="No data for given date")
    #                 return
    #             fitacf_data = fitacf_list[0]
            
    #         # Display the plot
    #         fig = create_range_time_plot(fitacf_data=fitacf_data, dataset_nbr=1, parameter=plot_type)

    #         canvas = FigureCanvasTkAgg(fig, master=self.plot_canvas_frame)
    #         canvas.draw()
    #         canvas.get_tk_widget().pack(fill="both", expand=True)
            

    #     except Exception as err :
    #         messagebox.showerror("Error: ", str(err))

    #     finally :
    #         self.plot_button.config(state="normal")

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


# # ------------------------------------------------
# # Reading and plotting functions
# def create_range_time_plot(fitacf_data, dataset_nbr:int, parameter:str) :
#     if parameter == "summary" :
#         pydarn.RTP.plot_summary(fitacf_data, 
#                                 beam_num=fitacf_data[dataset_nbr]['bmnum'],
#                                 range_estimation=pydarn.RangeEstimation.RANGE_GATE,
#                                 date_fmt='%H:%M'
#                                 )
#         plt.title("Radar {:d}, Beam {:d}".format(fitacf_data[dataset_nbr]['stid'], fitacf_data[dataset_nbr]['bmnum']))

#     elif parameter == 'v' :
#         pydarn.RTP.plot_range_time(fitacf_data, parameter='v',
#                                     beam_num=fitacf_data[dataset_nbr]['bmnum'], 
#                                     range_estimation=pydarn.RangeEstimation.RANGE_GATE, 
#                                     zmin=-500, zmax=500,
#                                     colorbar_label='Line of sight velocity (m/s)',
#                                     date_fmt='%H:%M'
#                                     )
#         plt.title("Radar {:d}, Beam {:d}".format(fitacf_data[dataset_nbr]['stid'], fitacf_data[dataset_nbr]['bmnum']))  
#         plt.ylabel('Range gates')
#         plt.xlabel('Time (UTC)')
    
#     elif parameter == "p_l" :
#         pydarn.RTP.plot_range_time(fitacf_data, parameter='p_l',
#                                     beam_num=fitacf_data[dataset_nbr]['bmnum'], 
#                                     range_estimation=pydarn.RangeEstimation.RANGE_GATE,
#                                     groundscatter=True,
#                                     zmax=0, zmin=40,
#                                     colorbar_label='Backscattered Power (dB)',
#                                     date_fmt='%H:%M'
#                                     )
#         plt.title("Radar {:d}, Beam {:d}".format(fitacf_data[dataset_nbr]['stid'], fitacf_data[dataset_nbr]['bmnum']))  
#         plt.ylabel('Range gates')
#         plt.xlabel('Time (UTC)')
    
#     elif parameter == 'w_l' :
#         pydarn.RTP.plot_range_time(fitacf_data, parameter='w_l', 
#                                     beam_num=fitacf_data[dataset_nbr]['bmnum'], 
#                                     range_estimation=pydarn.RangeEstimation.RANGE_GATE, 
#                                     colorbar_label='Spectral width (m/s)',
#                                     date_fmt='%H:%M'
#                                     )
#         plt.title("Radar {:d}, Beam {:d}".format(fitacf_data[dataset_nbr]['stid'], fitacf_data[dataset_nbr]['bmnum'])) 
#         plt.ylabel('Range gates')
#         plt.xlabel('Time (UTC)')

#     elif parameter == 'elv' :
#         pydarn.RTP.plot_range_time(fitacf_data, parameter='elv',
#                                     beam_num=fitacf_data[dataset_nbr]['bmnum'], 
#                                     range_estimation=pydarn.RangeEstimation.RANGE_GATE, 
#                                     colorbar_label='Elevation angle (deg)',
#                                     date_fmt='%H:%M'
#                                     )
#         plt.title("Radar {:d}, Beam {:d}".format(fitacf_data[dataset_nbr]['stid'], fitacf_data[dataset_nbr]['bmnum'])) 
#         plt.ylabel('Range gates')
#         plt.xlabel('Time (UTC)')
    
#     return plt.gcf()

# def read_fitacf3_entire_day(fitacf_dir:Path, date:dt.datetime) :
#     date_str = date.strftime('%Y%m%d')
#     fitacf_files = list(fitacf_dir.glob(f'{date_str}.*.fitacf'))
#     fitacf_files.sort()

#     concatenated_data = list()
#     for file in fitacf_files :
#         fitacf_data, _ = pydarn.read_fitacf(str(file))
#         concatenated_data += fitacf_data
    
#     return concatenated_data

# def list_fitacf3_files(fitacf_dir:Path, date:dt.datetime) :
#     date_str = date.strftime('%Y%m%d')
#     fitacf_files = list(fitacf_dir.glob(f'{date_str}.*.fitacf'))
#     fitacf_files.sort()

#     return fitacf_files


# ------------------------------------------------
# Making script executable
if __name__ == "__main__" :
    root = tk.Tk()
    app = PRIDE_GUI(root)
    root.mainloop()


