#!/usr/bin/env python3

"""
Read one single record and do something with it...
"""

import argparse
import numpy as np
import scipy.signal as ss
from datetime import datetime
import matplotlib.pyplot as plt
from numpy.fft import fftshift


def plot_spectrogram(x, fs, titletext=""):
    """Given a complex signal, plot its two-sided spectrogram"""
    f, t, Sxx = ss.spectrogram(x, fs, return_onesided=False)
    Syy = 10*np.log10(Sxx.squeeze())
    plt.pcolormesh(t, fftshift(f), fftshift(Syy, axes=0))
    plt.xlabel('t (s)')
    plt.ylabel('f (Hz)')
    plt.colorbar()
    plt.title(titletext)
    plt.show()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-file", type=str, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    # For a proper datafile, there should be a timestamp, sample frequency
    # and (complex)
    # data
    npzfile = np.load(args.input_file)
    print(npzfile.files)
    fs = npzfile['fs']
    filetimestamp = npzfile['timestamp']
    samples = npzfile['samples']

    mytimestamp = datetime.fromtimestamp(filetimestamp))
    print(mytimestamp)
    plot_spectrogram(samples, fs, mytimestamp.strftime("%Y-%m-%dT%H:%M:%S"))


if __name__ == "__main__":
    main()
