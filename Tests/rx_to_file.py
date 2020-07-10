import uhd
import numpy as np
import argparse

# A simple script based on the examples in the python API.
#
# The data are saved as a NumPy datafile. The USRP parameter defaults
# are the ones that will likely be used for receiving the CW transmissions
# from Hornsund at 4.45MHz. Furthermore, there is no need to use a very high
# sample frequency, so the smallest sample frequency possible for USRP N200
# is used.


def parse_args():
    parser = argparse.ArgumentParser(description="RX from USRP to file")
    parser.add_argument("-a", "--args", default="", type=str)
    parser.add_argument("-o", "--output-file", type=str, required=True)
    parser.add_argument("-f", "--freq", default=4.45e6, type=float)
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
    samps = usrp.recv_num_samps(num_samps, args.freq, args.rate,
                                args.channels, args.gain)
    with open(args.output_file, 'wb') as f:
        np.save(f, samps, allow_pickle=False, fix_imports=False)


if __name__ == "__main__":
    main()
