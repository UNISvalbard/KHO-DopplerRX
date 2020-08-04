"""
A quick script to produce a spectrogram from one hour datafiles. The
assumption is that the sampling rate has been constant and no samples are
missing (the latter of which is most likely not true always)

The data is imported as a NumPy datafile. When using the spectrogram
function, one should note that it returns a matrix that has "too many"
dimensions, which produces an error with pcolormesh if not taken care of.


"""

import scipy.signal as ss
from numpy.fft import fftshift
import matplotlib.pyplot as plt
import numpy as np
import argparse

"""
The suggested processing is to use overlapping 40-s windows to obtain
a spectrum every 10 seconds. So, for each window, there are 40*100=4000
samples (we'll use 4096). Let's try 50% overlap...
"""


def plot_spectrogram(x, fs):
    """Given a complex signal, plot its two-sided spectrogram"""

    f, t, Sxx = ss.spectrogram(x, fs, "hann",
                               nfft=2048, return_onesided=False,
                               scaling="spectrum")
    Syy = 10*np.log10(Sxx.squeeze())
    Syy = Syy-np.max(Syy)
    print("delta f =", f[1]-f[0])
    plt.pcolormesh(t, fftshift(f), fftshift(Syy, axes=0))
    plt.xlabel('t (s)')
    plt.ylabel('f (Hz)')
    plt.colorbar()
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
    # ts = mydata["timestamps"]
    iq = mydata["iq"]
    plot_spectrogram(iq, 100)


if __name__ == "__main__":
    main()
