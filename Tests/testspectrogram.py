#!/usr/bin/env python3

import scipy.signal as ss
from numpy.fft import fftshift
import matplotlib.pyplot as plt
import numpy as np
import argparse

# For a nice tutorial, see https://docs.python.org/3/howto/argparse.html


def parse_args():
    parser = argparse.ArgumentParser(description="Test spetrogram")
    parser.add_argument("-v", "--verbose", help="Increase verbosity",
                        action="store_true")
    parser.add_argument("-i", "--input-file", type=str,
                        required=True, help="Input file (NumPy data)")
    return parser.parse_args()


def main():
    args = parse_args()
    print(args)

    x = np.load(args.input_file)
    fs = 250e3
    f, t, Sxx = ss.spectrogram(x, fs, return_onesided=False)
    plt.pcolormesh(t, fftshift(f), fftshift(Sxx, axes=0))
    plt.xlabel('t (s)')
    plt.ylabel('f (Hz)')
    plt.show()


if __name__ == "__main__":
    main()
