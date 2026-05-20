#!/usr/bin/env python3


"""
A quick script to produce a spectrogram from one hour datafiles. The
assumption is that the sampling rate has been constant and no samples are
missing (the latter of which is most likely not true always).

The raw npz-files may have the samples in somewhat random order, so
one should sort them using the time stamps before doing anything else.

The data is imported as a NumPy datafile. When using the spectrogram
function, one should note that it returns a matrix that has "too many"
dimensions, which produces an error with pcolormesh if not taken care of.


"""

import scipy.signal as ss
from numpy.fft import fftshift
import matplotlib.pyplot as plt
import numpy as np
import argparse
import datetime as dt
import xarray as xr
import configparser
from pathlib import Path

"""
The suggested processing is to use overlapping 40-s windows to obtain
a spectrum every 10 seconds. So, for each window, there are 40*100=4000
samples (we'll use 4096). Let's try 50% overlap...
"""


def plot_spectrogram(ts, x, fs):
    """Given a complex signal, plot its two-sided spectrogram"""

    f, t, Sxx = ss.spectrogram(x, fs, "hann",
                               nfft=4096, return_onesided=False,
                               scaling="spectrum")
    
  #  fmin=15 #Hz, note that there is an offset between RX centre freq
  #  fmax=30 #to go around the DC component...
    
    fmin=-10
    fmax=10
    

    Syy = 10*np.log10(Sxx.squeeze())
    Syy = Syy-np.max(Syy)
    print("Spectral resolution delta f =", f[1]-f[0])
    plt.pcolormesh(t/60, fftshift(f), fftshift(Syy, axes=0),vmin=-80)
    plt.xlabel('t (min)')
    plt.ylabel('f (Hz)')
   # plt.ylim(fmin,fmax)
    plt.colorbar()

    starttime=dt.datetime.utcfromtimestamp(ts[0])
    plt.title(starttime.strftime("%Y-%m-%d %HUT"))
    plt.show()

    return f, t, Sxx, Syy

def parse_args():
    parser = argparse.ArgumentParser(description="Test spectrogram")
    parser.add_argument("-i", "--input-file", type=str,
                        required=True, help="Input file (NumPy data)")

    return parser.parse_args()


def plot_max_psd_vs_time(ts, x, fs):
    f, t, Sxx = ss.spectrogram(x, fs, "hann",
                               nfft=4096,
                               return_onesided=False,
                               scaling="spectrum")

    # Convert to dB
    Syy = 10 * np.log10(Sxx.squeeze())

    # Optional: normalize so strongest point is 0 dB
    Syy = Syy - np.max(Syy)

    # Find max PSD for each time bin
    max_psd = np.max(Syy, axis=0)

    # Find frequency where max occurs for each time bin
    max_index = np.argmax(Syy, axis=0)
    max_freq = f[max_index]

    # Convert spectrogram time to minutes
    time_minutes = t / 60

#remove the plotting code for now as it's not helpful
    # plt.figure()
    # plt.plot(time_minutes, max_psd)
    # plt.xlabel("Time (min)")
    # plt.ylabel("Maximum PSD (dB)")
    # plt.title("Maximum Spectral Power vs Time")
    # plt.grid(True)
    # plt.show()

    return time_minutes, max_psd, max_freq
	

def main():
    # args = parse_args()
    # filename = args.input_file
    config = configparser.ConfigParser()
    config.read('config.ini')
    filename = Path(config['spectrogram_1h-settings']['file_to_read'])

    # # To read hdf5 files
    # mydata = np.load(filename)
    # ts = mydata["timestamps"]
    # iq = mydata["iq"]

    # To read nc files
    mydata = xr.open_dataset(filename)
    ts = np.array(mydata['time'])
    iq = np.array(mydata['samples_I'] + mydata['samples_Q'] * 1j)

    ind = np.argsort(ts)
    ts_sorted = ts[ind]  # One gets funny looking spectrograms if the
    iq_sorted = iq[ind]  # samples are not in temporal order...
    fs = 100

    #plot the data that has not been filtered or downshited 
    f,t,Sxx,Syy = plot_spectrogram(ts_sorted, iq_sorted, fs)
    
    timestamps = ts_sorted
    sampleIQ = iq_sorted
  
    f_LO = -25      # complex frequency mixing to shift the signal down by -25Hz and add a low pass filter to get 
    y_LO = np.exp(1j * 2 * np.pi * f_LO * timestamps) # rid of frequencies we aren't interested in

    mixedIQ = sampleIQ * y_LO

    b, a = ss.butter(4, 20 / (fs / 2), btype='low')
    filteredIQ = ss.filtfilt(b, a, mixedIQ)
    
    f,t,Sxx,Syy = plot_spectrogram(timestamps, filteredIQ, fs)
    
    # Run spectrogram + extract peaks of the unfiltered data
    time_minutes, max_psd, max_freq = plot_max_psd_vs_time(ts_sorted, iq_sorted, fs)
   
    plt.figure()
    plt.plot(time_minutes, max_freq)
    plt.xlabel("Time (min)")
    plt.ylabel("Frequency of Maximum PSD (Hz)")
    plt.title("Frequency of Strongest Peak vs Time")
    plt.grid(True)
    plt.show()
    
    # Run spectrogram + extract peaks of the unfiltered data
    time_minutes, max_psd, max_freq = plot_max_psd_vs_time(timestamps, filteredIQ, fs)
   
    plt.figure()
    plt.plot(time_minutes, max_freq,'x',markersize=2)
    plt.xlabel("Time (min)")
    plt.ylabel("Frequency of Maximum PSD (Hz)")
    plt.title("Frequency of Strongest Peak vs Time - filtered and downshifted")
    plt.grid(True)
    plt.show()
    

    return mydata, ts, iq, ts_sorted, iq_sorted, f, t, Sxx, Syy

if __name__ == "__main__":
    mydata, ts, iq, ts_sorted, iq_sorted, f, t, Sxx, Syy = main()

    