#!/usr/bin/env python3

"""
Merge from the new onehour-datafiles into the main data
"""

import argparse
import numpy as np
import glob
import os
# import datetime as dt
import logging
# import pathlib


def parse_args():
    """ Either use defaults or get something from the user"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-n", "--dry-run", action="store_true")
    # parser.add_argument("-d", "--delete-files", action="store_true")
    parser.add_argument("-i", "--input-directory", required=True)
    parser.add_argument("-o", "--output-directory", default="/dev/shm/Doppler")
    return parser.parse_args()


# ------------------------------------------------------------------


def main():
    """ Process all individual datafiles into one-hour-files"""
    args = parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Verbose mode")

    searchpattern = os.path.join(args.input_directory, "**",
                                 "doppler_lyr_????????_??UT.npz")
    myfiles = glob.glob(searchpattern, recursive=True)
    myfiles.sort()

    for i in np.arange(0, len(myfiles)):
        print("Processing", myfiles[i])


if __name__ == "__main__":
    print("This script is nowhere near ready to be run")
    # main()
