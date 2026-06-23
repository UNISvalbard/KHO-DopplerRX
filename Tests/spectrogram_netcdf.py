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
        data_dict['freq'] = np.array(timeseries_dataset['frequency'])
        data_dict['max_freq'] = np.array(timeseries_dataset['max_freq'])
        data_dict['Syy_shifted'] = np.array(timeseries_dataset['Syy_shifted'])

        start_date_str = timeseries_dataset['time'].attrs['units'].split(' ')[2]
        start_date = dt.datetime.fromisoformat(start_date_str)


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
    

    # ------------------------------------------------
    # Run spectrogram + extract peaks of the filtered data

    data_dict = {}
    
    # complex frequency mixing to shift the signal down by -25Hz and add a low pass filter to get 
    # rid of frequencies we aren't interested in
    f_LO = -23
    y_LO = np.exp(1j * 2 * np.pi * f_LO * raw_timestamps) 
    mixed_IQ = samples_IQ * y_LO

    sos = ss.butter(4, 20/(sample_frequency/2), btype='low', output='sos')
    filtered_IQ = ss.sosfilt(sos, mixed_IQ)

    # Run spectrogram

    STF = ss.ShortTimeFFT.from_window('hann', fs=sample_frequency, nperseg=256, noverlap=32, fft_mode='twosided', mfft=4096, scale_to='psd')
    
    f = STF.f
    data_dict['freq'] = np.array(f)

    t = STF.t(len(filtered_IQ))
    data_dict['time'] = np.array(t)

    Sxx = STF.spectrogram(filtered_IQ)
    # Convert to dB and normalize so strongest point is 0 dB
    Syy = 10 * np.log10(Sxx.squeeze())
    Syy = Syy - np.max(Syy)
    data_dict['Syy_shifted'] = np.array(fftshift(Syy, axes=0))

    # Find frequency where max occurs for each time bin
    max_index = np.argmax(Syy, axis=0)
    data_dict['max_freq'] = np.array(f[max_index])


    # Replace sequences of 0 originating from missing data with NaNs
    zeros_filter = (data_dict['max_freq'] == 0)
    diff = np.diff(np.concatenate(([0], zeros_filter, [0])))
    sequence_starts = np.where(diff == 1)[0]
    sequence_ends = np.where(diff == -1)[0]
    for s, e in zip(sequence_starts, sequence_ends) :
        if e - s >= 2 :
            data_dict['max_freq'][s:e] = np.nan


    # ------------------------------------------------
    # Create the dataset, add metadata and save it to netcdf file

    # Time series
    prideds = xr.Dataset(coords={'time': data_dict['time'].astype(int), 
                                 'frequency': data_dict['freq']})
    
    prideds['Syy_shifted'] = (['frequency', 'time'], data_dict['Syy_shifted'])
    prideds['max_freq'] = ("time", data_dict['max_freq'])

    # Metadata
    prideds['time'].attrs = {
        'standard_name':'time',
        'long_name': 'time',
        'units': f'seconds since {start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}',
        'calendar': 'standard',
        'coverage_content_type': 'coordinate'
    }

    prideds['frequency'].attrs = {
        'standard_name':'frequency',
        'long_name': 'frequency',
        'units': f'Hertz',
        'calendar': 'standard',
        'coverage_content_type': 'coordinate'
    }

    prideds['Syy_shifted'].attrs = {
        'long_name': 'Spectrogram power',
        'units': 'dB',
        'coverage_content_type': 'physicalMeasurement'
    }

    prideds['max_freq'].attrs = {
        'long_name': 'Frequency of maximum power',
        'units': 'Hz',
        'coverage_content_type': 'physicalMeasurement'
    }

    # Export to netcdf
    time_series_file = destination_folder / f'test_PRIDE_spectrogram_{start_date.strftime('%Y%m%d')}.nc'

    encoding = {
        'time': {
            'dtype': 'float64',
            '_FillValue': None  # Coordinate variables should not have fill values.
        },
        'frequency':{
            'dtype': 'float64',
            '_FillValue': None
        },
        'Syy_shifted':{
            'dtype': 'float64',
            '_FillValue': None
        },
        'max_freq': {
            'dtype': 'float64',
            '_FillValue': None
        }
    }

    prideds.to_netcdf(time_series_file, encoding=encoding)


# ------------------------------------------------
# Plot the obtained data

if args.plot_spectrogram :
    # Unpack data 
    data_dict['timestamps'] = np.array([start_date + dt.timedelta(milliseconds=int(data_dict['time'][k]*1000)) for k in range(len(data_dict['time']))])
    time = data_dict['timestamps']
    frequency = data_dict['freq']
    max_psd = data_dict['max_freq']
    syy = data_dict['Syy_shifted']

    f_decim = 4
    t_decim = 16

    # Avoid using matplotlib.pyplot as it prevents tkinter window from closing
    fig = plt.figure(figsize=(15, 5))
    ax0 = fig.add_subplot(2, 1, 1)
    ax1 = fig.add_subplot(2, 1, 2)
    fig.subplots_adjust(bottom=0.2)

    # Spectrogram plot
    spectrogram = ax0.imshow(syy[::f_decim, ::t_decim], 
                             aspect='auto', origin='lower', interpolation='nearest')
    # colorbar = fig.colorbar(spectrogram)
    # colorbar.set_label('Received power')
    ax0.set_title(f'Spectrogram')
    ax0.set_ylabel('Frequency (Hz)')
    ax0.get_xaxis().set_visible(False)

    # Maximum PSD plot
    psd_plot, = ax1.plot(time[::t_decim], max_psd[::t_decim], linestyle='None', marker='+', markersize=4)
    ax1.set_xlim(time[0], time[-1])
    ax1.set_autoscale_on(False)

    ax1.set_title(f"Frequency of Strongest Peak vs Time - filtered and downshifted - {start_date.strftime('%Y/%m/%d')}")
    ax1.set_ylabel("Frequency of Maximum PSD (Hz)")
    ax1.grid(alpha=0.3)

    ax1.set_xlabel("Time")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))


    # Slider definition and fig update 
    window_width = dt.timedelta(hours=1)
    ax_slider = fig.add_axes(rect=(0.1, 0.05, 0.8, 0.03))
    slider = Slider(ax=ax_slider, label="Displayed hour", valmin=0, valmax=1, valinit=0)

    def format_time(val) : 
        return time[0] + val * (time[-1] - dt.timedelta(hours=1) - time[0])

    slider.valtext.set_text(f"{format_time(slider.val).strftime('%H:%M')}")


    # Update function
    def update(val) :
        start_display = format_time(slider.val)
        end_display = start_display + window_width
        time_filter = (time >= start_display) & (time < end_display)

        # Filter and decimate the data
        spectrogram.set_data(syy[:, time_filter][::f_decim, ::2])
        psd_plot.set_data(time[time_filter], max_psd[time_filter])

        ax1.set_xlim(start_display, end_display)
        slider.valtext.set_text(f"{start_display.strftime('%H:%M')}")
    slider.on_changed(update)


    # Handling function for the mouse wheel
    def on_scroll(event) :
        if event.inaxes == ax_slider or event.inaxes in (ax0, ax1) :
            current_val = slider.val
            step = 0.005
            
            if event.step < 0:
                new_val = min(current_val + step, slider.valmax)
            else:
                new_val = max(current_val - step, slider.valmin)
                
            slider.set_val(new_val)
    fig.canvas.mpl_connect('scroll_event', on_scroll)

    # fig.tight_layout()

    plt.show()