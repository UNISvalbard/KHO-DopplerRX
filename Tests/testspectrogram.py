#!/usr/bin/env python3

# A quick script to produce a spectrogram from data captured using
# rx_to_file.py
#
# The data is imported as a NumPy datafile. When using the spectrogram
# function, one should note that it returns a matrix that has "too many"
# dimensions, which produces an error with pcolormesh if not taken care of.
"""
Plot a spectrogram of data captured with rx_to_file.py
"""

import scipy.signal as ss
from numpy.fft import fftshift
import matplotlib.pyplot as plt
import numpy as np
import argparse


def plot_spectrogram(x, fs):
    """Given a complex signal, plot its two-sided spectrogram"""
    f, t, Sxx = ss.spectrogram(x, fs, return_onesided=False)
    Syy = 10*np.log10(Sxx.squeeze())
    plt.pcolormesh(t, fftshift(f), fftshift(Syy, axes=0))
    plt.xlabel('t (s)')
    plt.ylabel('f (Hz)')
    plt.colorbar()
    plt.show()

# For command line running, there are a number of arguments that
# might be useful for testing


def parse_args():
    parser = argparse.ArgumentParser(description="Test spectrogram")
    parser.add_argument("-v", "--verbose", help="Increase verbosity",
                        action="store_true")
    parser.add_argument("-i", "--input-file", type=str,
                        required=True, help="Input file (NumPy data)")
    return parser.parse_args()


def main():
    args = parse_args()
    # print(args)

    x = np.load(args.input_file)
    fs = 250e3
    plot_spectrogram(x, fs)


if __name__ == "__main__":
    main()
