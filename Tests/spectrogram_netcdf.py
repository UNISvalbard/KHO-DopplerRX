"""
Created on Thu May 21

@author: Olivier

This script takes in a raw 24h PRIDE netcdf file and creates a spectrogram.
The spectrogram is saved as a time series in a netcdf file.
The spectrogram can also be plotted by the script using flag
"""

import scipy.signal as ss
from numpy.fft import fftshift
import matplotlib.pyplot as plt
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
filename = Path(config['spectrogram_netcdf-settings']['file_to_read'])


# ------------------------------------------------
# Read 24h netcdf data file

raw_dataset = xr.open_dataset(filename, decode_cf=False)

ms_since_start = np.array(raw_dataset['time'])
start_date_str = raw_dataset['time'].attrs['units'].split(' ')[2]
start_timestamp = dt.datetime.fromisoformat(start_date_str).timestamp()

timestamps = ms_since_start/1000 + start_timestamp
samples_IQ = np.array(raw_dataset['samples_I'] + raw_dataset['samples_Q'] * 1j)

order = np.argsort(timestamps)
timestamps = timestamps[order]  # One gets funny looking spectrograms if the
samples_IQ = samples_IQ[order]  # samples are not in temporal order...
sample_frequency = 100


# ------------------------------------------------
# Run spectrogram + extract peaks of the unfiltered data

f, t, Sxx = ss.spectrogram(samples_IQ, sample_frequency, "hann", nfft=4096, return_onesided=False, scaling="spectrum")

# Convert to dB and normalize so strongest point is 0 dB
Syy = 10 * np.log10(Sxx.squeeze())
Syy = Syy - np.max(Syy)

# Find frequency where max occurs for each time bin
max_index = np.argmax(Syy, axis=0)
max_freq = f[max_index]

# # Convert spectrogram time to minutes
# time_minutes = t / 60

