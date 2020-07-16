#!/usr/bin/env python3

"""
Combine the raw data files into one hour datafiles
- go through all available data in the directory where the
  streaming script saves data
- create the hourly data file if it missing
- add the data from the current file to the new hourly file,
  but only if there is no data from those times already
"""

import argparse
import numpy as np
import glob
import os
import datetime as dt
import logging


def parse_args():
    """ Either use defaults or get something from the user"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-d", "--delete-files", action="store_true")
    parser.add_argument("-i", "--input-directory", required=True)
    parser.add_argument("-o", "--output-directory", default="/dev/shm")
    return parser.parse_args()


def save_to_hour_file(filename, tindex, samples):
    """Save/merge data to one hour datafiles"""
    logging.debug("\t -> ", filename)
    if os.path.exists(filename):
        logging.debug("\tMerging to existing data...")
        old_data = np.load(filename)
        old_tindex = old_data["timestamps"]
        if np.all(np.in1d(tindex, old_tindex)):
            logging.debug("\t - data exists, nothing merged")
            return
        else:
            logging.debug("\t - merging")
            tindex = np.concatenate((tindex, old_tindex))
            samples = np.concatenate((samples, old_data["iq"]))

    np.savez_compressed(filename, timestamps=tindex, iq=samples)


def savecheck(filename, tindex, samples):
    """ For checking that the indices go right... """
    print("Would be saving to", filename)
    tsmin = dt.datetime.fromtimestamp(np.min(tindex))
    tsmax = dt.datetime.fromtimestamp(np.max(tindex))
    print("with a range from", tsmin, "to", tsmax)


def main():
    args = parse_args()
    # print(args)
    logging.basicConfig(level=logging.INFO)
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    myfiles = glob.glob(os.path.join(args.input_directory, "*.npz"))
    myfiles.sort()

    for i in np.arange(0, len(myfiles)):
        print("Processing", myfiles[i])
        thisdata = np.load(myfiles[i])
        samples = thisdata["samples"]
        ts = thisdata["timestamp"]
        fs = thisdata["fs"]
        delta = 1/fs

        # The timestamp in the data file is for the first sample, so
        # we can use the fact that the rest of the samples are sampled
        # at a regular rate. So, the data goes either to one hour-file
        # only or some part of it will need to written to the following
        # hour-file
        tindex = ts+np.arange(0, samples.size)*delta
        mintime = dt.datetime.fromtimestamp(np.min(tindex))
        maxtime = dt.datetime.fromtimestamp(np.max(tindex))

        filename = mintime.strftime("/dev/shm/doppler_lyr_%Y%m%d_%HUT.npz")
        filename_ext = maxtime.strftime("/dev/shm/doppler_lyr_%Y%m%d_%HUT.npz")
        filename = os.path.join(args.output_directory, filename)
        filename_ext = os.path.join(args.output_directory, filename_ext)

        if filename == filename_ext:
            save_to_hour_file(filename, tindex, samples)
        else:
            firsthour = dt.datetime.fromtimestamp(tindex[0]).hour
            secondhour = dt.datetime.fromtimestamp(tindex[1]).hour
            j = 1
            while firsthour == secondhour:
                j = j+1
                secondhour = dt.datetime.fromtimestamp(tindex[j]).hour
            firsthour_end = j-1
            secondhour_start = j
            save_to_hour_file(filename, tindex[0:firsthour_end],
                              samples[0:firsthour_end])
            save_to_hour_file(filename_ext, tindex[secondhour_start:],
                              samples[secondhour_start:])

        if args.delete_files:
            logging.debug("\t - old file removed")


if __name__ == "__main__":
    main()
