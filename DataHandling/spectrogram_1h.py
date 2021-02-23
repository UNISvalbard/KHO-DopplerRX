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
    
    fmin=15 #Hz, note that there is an offset between RX centre freq
    fmax=30 #to go around the DC component...
    

    Syy = 10*np.log10(Sxx.squeeze())
    Syy = Syy-np.max(Syy)
    print("Spectral resolution delta f =", f[1]-f[0])
    plt.pcolormesh(t/60, fftshift(f), fftshift(Syy, axes=0),vmin=-80)
    plt.xlabel('t (min)')
    plt.ylabel('f (Hz)')
    plt.ylim(fmin,fmax)
    plt.colorbar()

    starttime=dt.datetime.utcfromtimestamp(ts[0])
    plt.title(starttime.strftime("%Y-%m-%d %HUT"))
    plt.show()


def parse_args():
    parser = argparse.ArgumentParser(description="Test spectrogram")
    parser.add_argument("-i", "--input-file", type=str,
                        required=True, help="Input file (NumPy data)")

    return parser.parse_args()


def main():
    args = parse_args()
    filename = args.input_file
    mydata = np.load(filename)
    ts = mydata["timestamps"]
    iq = mydata["iq"]
    ind = np.argsort(ts)
    ts_sorted = ts[ind]  # One gets funny looking spectrograms if the
    iq_sorted = iq[ind]  # samples are not in temporal order...
    plot_spectrogram(ts_sorted, iq_sorted, 100)


if __name__ == "__main__":
    main()

