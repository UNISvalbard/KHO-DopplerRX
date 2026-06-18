"""
Created on Thu May 21

@author: Olivier

This script is based on existing code found in spectrogram_1h.py and netcdf-metadata.py

Default comportment :
This script takes in a raw 24h PRIDE netcdf file and creates a spectrogram.
This results in a time series which is then refined and saved in a netcdf file.

Flags :
-p : This is used to plot the spectrogram in a 24h format.
-r : This is used to read an existing time series instead of reading the rawdata and computing the spectrogram again. 
     N.B.: this flag should be used alongside the -p flag, otherwise nothing happens
"""

import scipy.signal as ss
from numpy.fft import fftshift
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import matplotlib.dates as mdates
import numpy as np
import datetime as dt
import xarray as xr
from pathlib import Path
import argparse
import configparser


# ------------------------------------------------
# Read config and parse args

config = configparser.ConfigParser()
config.read('config.ini')
raw_data_folder = Path(config['spectrogram_netcdf-settings']['raw_data_folder'])
destination_folder = Path(config['spectrogram_netcdf-settings']['destination_folder'])
str_date = config['spectrogram_netcdf-settings']['date']

parser = argparse.ArgumentParser(description="Test spectrogram")
parser.add_argument("-p", "--plot-spectrogram", default=False, action=argparse.BooleanOptionalAction)
parser.add_argument("-r", "--read-timeseries", default=False, action=argparse.BooleanOptionalAction)
parser.add_argument("-d", "--date", default=str_date)
args = parser.parse_args()

str_date = args.date

date = dt.datetime.strptime(str_date, '%Y/%m/%d')

# ------------------------------------------------
# Read existing time-series if chosen to

if args.read_timeseries :
    time_series_file = destination_folder / f'test_PRIDE_spectrogram_{date.strftime('%Y%m%d')}.nc'
    with xr.open_dataset(time_series_file, decode_cf=False) as timeseries_dataset :

        data_dict = {}
        data_dict['time'] = np.array(timeseries_dataset['time'])
        data_dict['max_freq'] = np.array(timeseries_dataset['max_freq'])

        start_date_str = timeseries_dataset['time'].attrs['units'].split(' ')[2]
        start_date = dt.datetime.fromisoformat(start_date_str)
        data_dict['timestamps'] = np.array([start_date + dt.timedelta(seconds=int(data_dict['time'][k])) for k in range(len(data_dict['time']))])


# ------------------------------------------------
# Read raw netcdf data file and create spectrogram timeseries (Default)

else :
    raw_data_file = raw_data_folder / f'test_PRIDE_{date.strftime('%Y%m%d')}.nc'
    with xr.open_dataset(raw_data_file, decode_cf=False) as raw_dataset :

        ms_since_start = np.array(raw_dataset['time'])
        start_date_str = raw_dataset['time'].attrs['units'].split(' ')[2]
        start_date = dt.datetime.fromisoformat(start_date_str)

        raw_timestamps = ms_since_start/1000 + start_date.timestamp()
        samples_IQ = np.array(raw_dataset['samples_I'] + raw_dataset['samples_Q'] * 1j)

        order = np.argsort(raw_timestamps)
        raw_timestamps = raw_timestamps[order]  # One gets funny looking spectrograms if the
        samples_IQ = samples_IQ[order]  # samples are not in temporal order...
        sample_frequency = 100
    
    # complex frequency mixing to shift the signal down by -25Hz and add a low pass filter to get 
    # rid of frequencies we aren't interested in
    f_LO = -25
    y_LO = np.exp(1j * 2 * np.pi * f_LO * raw_timestamps) 
    sos = ss.butter(4, 20/(sample_frequency/2), btype='low', output='sos')
    mixed_IQ = samples_IQ * y_LO


    # ------------------------------------------------
    # Run spectrogram + extract peaks of the filtered data

    data_dict = {}
    data_dict['max_freq'] = []
    data_dict['time'] = []

    # Split the process in 24 hours to avoid computer explosion
    for i in range(24) :
        hour_selector = (raw_timestamps >= raw_timestamps[0] + i*3600) & (raw_timestamps < raw_timestamps[0] + (i + 1)*3600)

        filtered_IQ = ss.sosfilt(sos, mixed_IQ[hour_selector])
        f, t, Sxx = ss.spectrogram(filtered_IQ, sample_frequency, "hann", nfft=4096, return_onesided=False, scaling="spectrum")

        # Convert to dB and normalize so strongest point is 0 dB
        Syy = 10 * np.log10(Sxx.squeeze())
        Syy = Syy - np.max(Syy)

        # Find frequency where max occurs for each time bin
        max_index = np.argmax(Syy, axis=0)
        data_dict['max_freq'].append(f[max_index])
        
        data_dict['time'].append(t + i*3600)

    for key in data_dict.keys() :
        data_dict[key] = np.concatenate(data_dict[key], axis=0)
    
    # Replace sequences of 0 originating from missing data with NaNs
    zeros_filter = (data_dict['max_freq'] == 0)
    diff = np.diff(np.concatenate(([0], zeros_filter, [0])))
    sequence_starts = np.where(diff == 1)[0]
    sequence_ends = np.where(diff == -1)[0]
    for s, e in zip(sequence_starts, sequence_ends) :
        if e - s >= 2 :
            data_dict['max_freq'][s:e] = np.nan

    data_dict['timestamps'] = np.array([start_date + dt.timedelta(seconds=int(data_dict['time'][k])) for k in range(len(data_dict['time']))])


    # ------------------------------------------------
    # Create the dataset, add metadata and save it to netcdf file

    prideds = xr.Dataset()

    # Time series
    prideds = xr.Dataset(coords={'time': data_dict['time'].astype(int)})
    prideds['max_freq'] = ("time", data_dict['max_freq'])

    # Metadata
    prideds['time'].attrs = {
        'standard_name':'time',
        'long_name': 'time',
        'units': f'seconds since {start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}',
        'calendar': 'standard',
        'coverage_content_type': 'coordinate'
    }

    prideds['max_freq'].attrs = {
        'long_name': 'Maximum frequency',
        'units': 'Hz',
        'coverage_content_type': 'physicalMeasurement'
    }

    # Export to netcdf
    time_series_file = destination_folder / f'test_PRIDE_spectrogram_{start_date.strftime('%Y%m%d')}.nc'

    encoding = {
        'time': {
            'dtype': 'int64',
            '_FillValue': None  # Coordinate variables should not have fill values.
        },
        'max_freq': {
            'dtype': 'float64',
            '_FillValue': None
        },
    }

    prideds.to_netcdf(time_series_file, encoding=encoding)


# ------------------------------------------------
# Plot the obtained data

if args.plot_spectrogram :
    fig, ax = plt.subplots(figsize=(18, 5))
    plt.subplots_adjust(bottom=0.2)

    x_data = data_dict['timestamps']

    ax.plot(x_data, data_dict['max_freq'], linestyle='None', marker='+', markersize=4)
    ax.set_xlim(x_data[0], x_data[-1])
    ax.set_autoscale_on(False)

    ax.set_title(f"Frequency of Strongest Peak vs Time - filtered and downshifted - {start_date.strftime('%Y/%m/%d')}")
    ax.set_xlabel("Time")
    ax.set_ylabel("Frequency of Maximum PSD (Hz)")
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))


    # Slider definition and fig update 
    window_width = dt.timedelta(hours=1)
    ax_slider = plt.axes([0.1, 0.05, 0.8, 0.03])
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

    plt.show()