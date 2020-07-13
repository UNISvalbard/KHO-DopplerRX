#!/usr/bin/env python3

import uhd
import numpy as np
import argparse
import scipy.signal as ss

# A simple script based on the examples in the python API.
#
# The data are saved as a NumPy datafile.
#
# The defaults are for the NRK AM broadcast in Svalbard


def parse_args():
    parser = argparse.ArgumentParser(description="RX from USRP to file")
    parser.add_argument("-a", "--args", default="", type=str)
    parser.add_argument("-o", "--output-file", type=str, required=True)
    parser.add_argument("-f", "--freq", default=1.485e6, type=float)
    parser.add_argument("-r", "--rate", default=250e3, type=float)
    parser.add_argument("-d", "--duration", default=10.0, type=float)
    parser.add_argument("-c", "--channels", default=0, nargs="+", type=int)
    parser.add_argument("-g", "--gain", type=int, default=10)
    return parser.parse_args()


def main():
    args = parse_args()
    usrp = uhd.usrp.MultiUSRP(args.args)
    num_samps = int(np.ceil(args.duration*args.rate))
    if not isinstance(args.channels, list):
        args.channels = [args.channels]
    print("Recording...")
    samps = usrp.recv_num_samps(num_samps, args.freq, args.rate,
                                args.channels, args.gain)
    print("...done.")

    # For a normal AM station, the bandwidth is about +-18kHz around
    # the carrier wave, so we can reduce the bandwidth quite a bit
    f_target = 2*18e3    # Desired sample frequency
    q = int(args.rate/f_target)
    fs_new = args.rate/q
    print(fs_new)
    samps2 = ss.decimate(samps, q)
    with open(args.output_file, 'wb') as f:
        np.save(f, samps2, allow_pickle=False, fix_imports=False)


if __name__ == "__main__":
    main()
