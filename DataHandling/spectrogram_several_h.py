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
import matplotlib.dates as mdates
import numpy as np
#import argparse
import datetime as dt
import os
import glob
import sys

"""
The suggested processing is to use overlapping 40-s windows to obtain
a spectrum every 10 seconds. With fs=100Hz, using N=4096 results in a pretty
close approximation of 40-s window.

When using decimation factor of 4, fs=25Hz and a 40-s window would be
roughly 1024 samples

"""


def plot_spectrogram(starttime,stoptime,ts, x, fs):
    """Given a complex signal, plot its two-sided spectrogram"""

    f, t, Sxx = ss.spectrogram(x, fs, "hann",
                               nfft=1024, return_onesided=False,
                               scaling="spectrum")

    # fmin=15 #Hz, note that there is an offset between RX centre freq
    # fmax=30 #to go around the DC component...


    # There may be zeros in the data: we are limiting the plot down to -80dB
    # so we add a small positive value to the IQ data to avoid trying to
    # take a logarithm of zero...
    Syy = 10*np.log10(Sxx.squeeze()+sys.float_info.min)
    Syy = Syy-np.max(Syy)
    print("Spectral resolution delta f =", f[1]-f[0], 'Hz')


    timespan=[starttime+dt.timedelta(seconds=s) for s in t]

    fig,axs = plt.subplots()
    im=axs.pcolormesh(timespan, fftshift(f), fftshift(Syy, axes=0),vmin=-80)

    axs.set_xlabel('Time (UTC)')
    axs.set_ylabel('f (Hz)')
    #axs.ylim(fmin,fmax)
    fig.colorbar(im, label='Power (dB)')

    axs.set_title(starttime.strftime("%Y-%m-%d"))
    axs.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    axs.xaxis.set_tick_params(rotation=45)
    #axs.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
    #axs.xaxis.set_minor_locator(mdates.MinuteLocator(interval=30))
    axs.set_xlim(starttime,stoptime)
    plt.show()

"""
The following is mostly experimenting with several hours worth of data

TODO: one should fill in "empty hours", so rather than globbing for
existing hourly files, it'd be better to deterministically go through
the whole day from 00UT to 23UT

TODO: make this script read also HDF5-files...

"""
basedir=os.path.join('t:\\','PRIDE')
year=2024
month=5
day=1
daydir=os.path.join(basedir,f'{year:04}',f'{month:02}',f'{day:02}')
datafiles=glob.glob(os.path.join(daydir,'*nogaps.npz'))

datafiles=glob.glob('*nogaps.npz')

day_ts=[]
day_iq=[]
for filename in datafiles:
    print(f'Reading {filename}')
    mydata = np.load(filename)
    ts = mydata["timestamps"]
    iq = mydata["iq"]
    day_ts=np.concatenate((day_ts,ts))
    day_iq=np.concatenate((day_iq,iq))

ind = np.argsort(day_ts)
ts_sorted = day_ts[ind]  # One gets funny looking spectrograms if the
iq_sorted = day_iq[ind]  # samples are not in temporal order...

starttime=dt.datetime.fromtimestamp(ts_sorted[0],tz=dt.timezone.utc)
stoptime=dt.datetime.fromtimestamp(ts_sorted[-1],tz=dt.timezone.utc)

# The receiver is tuned 25Hz below the actual signal to avoid
# the DC spice in spectrum, but that means we need to shift the
# spectrum down by 25Hz.
# Also, the original 100Hz sampling frequency is unnecessarily
# large and we can speed up the processing by decimating. The basic
# decimation also takes care of lowpass filtering that usually
# follows mixing.

print("Mixing...")
f_LO=-25; # The LO frequency
y_LO=np.exp(1j*2*np.pi*f_LO*ts_sorted);

mixedIQ=iq_sorted*y_LO; # Complex mixing

print("Decimating...")
fs=100 # Hz
q=3 # Decimation factor

ts_decim=ss.decimate(ts_sorted,q)
iq_decim=ss.decimate(mixedIQ,q)

print("Plotting...")
plot_spectrogram(starttime,stoptime,ts_decim, iq_decim, fs/q)


