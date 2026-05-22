"""
Created on Thu May 21

@author: Olivier

This script is based on existing code found in spectrogram_1h.py

This script takes in a raw 24h PRIDE netcdf file and creates a spectrogram.
The spectrogram is saved as a time series in a netcdf file.
The spectrogram can also be plotted by the script using flag
"""

import scipy.signal as ss
from numpy.fft import fftshift
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np
import datetime as dt
import xarray as xr
from pathlib import Path
import argparse
import configparser


# ------------------------------------------------
# Read config and parse args

parser = argparse.ArgumentParser(description="Test spectrogram")
parser.add_argument("-p", "--plot-spectrogram", default=False, action=argparse.BooleanOptionalAction)
args = parser.parse_args()

config = configparser.ConfigParser()
config.read('config.ini')
raw_data_file = Path(config['spectrogram_netcdf-settings']['raw_data_file'])
destination_folder = Path(config['spectrogram_netcdf-settings']['destination_folder'])


# ------------------------------------------------
# Read 24h netcdf data file

with xr.open_dataset(raw_data_file, decode_cf=False) as raw_dataset :

    ms_since_start = np.array(raw_dataset['time'])
    start_date_str = raw_dataset['time'].attrs['units'].split(' ')[2]
    start_date = dt.datetime.fromisoformat(start_date_str)

    timestamps = ms_since_start/1000 + start_date.timestamp()
    samples_IQ = np.array(raw_dataset['samples_I'] + raw_dataset['samples_Q'] * 1j)

    order = np.argsort(timestamps)
    timestamps = timestamps[order]  # One gets funny looking spectrograms if the
    samples_IQ = samples_IQ[order]  # samples are not in temporal order...
    sample_frequency = 100


# ------------------------------------------------
# Run spectrogram + extract peaks of the unfiltered data

data_dict = {}
data_dict['max_freq'] = []
data_dict['time'] = []

# Split the process in 24 hours to avoid computer explosion
for i in range(24) :
    hour_selector = (timestamps >= timestamps[0] + i*3600) & (timestamps < timestamps[0] + (i + 1)*3600)

    f, t, Sxx = ss.spectrogram(samples_IQ[hour_selector], sample_frequency, "hann", nfft=4096, return_onesided=False, scaling="spectrum")

    # Convert to dB and normalize so strongest point is 0 dB
    Syy = 10 * np.log10(Sxx.squeeze())
    Syy = Syy - np.max(Syy)

    # Find frequency where max occurs for each time bin
    max_index = np.argmax(Syy, axis=0)
    data_dict['max_freq'].append(f[max_index])
    data_dict['time'].append(t + i*3600)

    print(f'Spectrogram {i+1} done.')

for key in data_dict.keys() :
    data_dict[key] = np.concatenate(data_dict[key], axis=0)


# # ------------------------------------------------
# # Create the dataset, add metadata and save it to netcdf file

# prideds = xr.Dataset()

# # Time series
# prideds = xr.Dataset(coords={'time': data_dict['time']})
# prideds['max_freq'] = ("time", data_dict['max_freq'])

# # Metadata
# prideds['time'].attrs = {
#     'standard_name':'time',
#     'long_name': 'time',
#     'units': f'seconds since {start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}',
#     'calendar': 'standard',
#     'coverage_content_type': 'coordinate'
# }

# prideds['max_freq'].attrs = {
#     'long_name': 'Maximum frequency',
#     'units': 'Hz',
#     'coverage_content_type': 'physicalMeasurement'
# }

# # Export to netcdf
# time_series_file = destination_folder / f'test_PRIDE_spectrogram_{start_date.strftime('%Y%m%d')}.nc'

# encoding = {
#     'time': {
#         'dtype': 'int64',
#         '_FillValue': None  # Coordinate variables should not have fill values.
#     },
#     'max_freq': {
#         'dtype': 'float64',
#         '_FillValue': None
#     },
# }

# prideds.to_netcdf(time_series_file, encoding=encoding)


# ------------------------------------------------
# Plot the obtained data

# # Matrix of spectrograms via matplotlib
# if args.plot_spectrogram :

#     fig, ax = plt.subplots(nrows=12, ncols=2, sharex=False, figsize=(28, 24))

#     for i in range(24) :
#         ax[i%12][i//12].plot(data_dict['time'][i], data_dict['max_freq'][i], 'x', markersize=2)
        
#         fig.supylabel("Frequency of Maximum PSD (Hz)")
#     fig.supxlabel("Time (s)")
#     fig.suptitle("Frequency of Strongest Peak vs Time - filtered and downshifted")

#     plt.tight_layout()
#     plt.show()


# Scrollable matplotlib specrtogram on 24h
if args.plot_spectrogram :
    fig, ax = plt.subplots(figsize=(18, 5))
    plt.subplots_adjust(bottom=0.2)

    ax.scatter(x=data_dict['time'], y=data_dict['max_freq'], marker='+', s=15)

    ax.set_title(f"Frequency of Strongest Peak vs Time - filtered and downshifted - {start_date.strftime('%Y/%m/%d')}")
    ax.set_xlabel("Hour of the day")
    ax.set_ylabel("Frequency of Maximum PSD (Hz)")
    ax.set_xlim(0, 86400)

    # Slider definition
    window_width = 3600
    ax_slider = plt.axes([0.1, 0.05, 0.8, 0.03])
    slider = Slider(ax=ax_slider, label="", valmin=0, valmax=86400 - window_width, valinit=0)

    def update(val):
        start = slider.val
        ax.set_xlim(start, start + window_width)
        fig.canvas.draw_idle()

    slider.on_changed(update)
    plt.show()