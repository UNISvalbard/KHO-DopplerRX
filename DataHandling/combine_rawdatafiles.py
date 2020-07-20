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
import pathlib


def parse_args():
    """ Either use defaults or get something from the user"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-n", "--dry-run", action="store_true")
    parser.add_argument("-d", "--delete-files", action="store_true")
    parser.add_argument("-i", "--input-directory", required=True)
    parser.add_argument("-o", "--output-directory", default="/dev/shm/Doppler")
    return parser.parse_args()

# The following code uses a shortcut, where we assume that
# there are no overlaps between the raw IQ files. So, if one or more of the
# samples are missing from the hourly file, then all samples from the
# raw datafile are added to that hour. Perhaps a better way would be
# to raise an exception if the merge would result in duplicate samples?


def save_to_hour_file(path, filename, tindex, samples):
    """Save/merge data to one hour datafiles"""
    fullfilename = os.path.join(path, filename)
    logging.debug(" -> " + fullfilename)

    if os.path.exists(path) is False:
        logging.debug(" ->  Creating a new directory " + path)
        pathlib.Path(path).mkdir(parents=True)

    if os.path.exists(fullfilename):
        logging.debug("\tMerging to existing data...")
        old_data = np.load(fullfilename)
        old_tindex = old_data["timestamps"]
        if np.all(np.in1d(tindex, old_tindex)):
            logging.debug("\t - all data exists already, nothing merged")
            return
        else:
            logging.info("\t - merging")
            tindex = np.concatenate((tindex, old_tindex))
            samples = np.concatenate((samples, old_data["iq"]))

    np.savez_compressed(fullfilename, timestamps=tindex, iq=samples)


def savecheck(path, filename, tindex, samples):
    """ For checking that the indices go right... """
    print("Would be saving to", os.path.join(path, filename))
    tsmin = dt.datetime.utcfromtimestamp(np.min(tindex))
    tsmax = dt.datetime.utcfromtimestamp(np.max(tindex))
    print("with a range from", tsmin, "to", tsmax)

# ------------------------------------------------------------------


def main():
    """ Process all individual datafiles into one-hour-files"""
    args = parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Verbose mode")

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
        # at a regular rate. So, the data goes either to one single
        # hour-file or some part of it will need to written to the following
        # hour-file
        tindex = ts+np.arange(0, samples.size)*delta
        mintime = dt.datetime.utcfromtimestamp(np.min(tindex))
        maxtime = dt.datetime.utcfromtimestamp(np.max(tindex))

        filename = mintime.strftime("doppler_lyr_%Y%m%d_%HUT.npz")
        filename_ext = maxtime.strftime("doppler_lyr_%Y%m%d_%HUT.npz")
        path = os.path.join(args.output_directory,
                            mintime.strftime("%Y"), mintime.strftime("%m"),
                            mintime.strftime("%d"))
        path_ext = os.path.join(args.output_directory,
                                maxtime.strftime("%Y"), maxtime.strftime("%m"),
                                maxtime.strftime("%d"))

        if filename == filename_ext:
            if args.dry_run:
                savecheck(path, filename, tindex, samples)
            else:
                save_to_hour_file(path, filename, tindex, samples)
        else:
            """ First, find the index where the hour changes"""
            firsthour = dt.datetime.utcfromtimestamp(tindex[0]).hour
            secondhour = dt.datetime.utcfromtimestamp(tindex[1]).hour
            j = 1
            while firsthour == secondhour:
                j = j+1
                secondhour = dt.datetime.utcfromtimestamp(tindex[j]).hour
            firsthour_end = j-1
            secondhour_start = j
            if args.dry_run:
                savecheck(path, filename,
                          tindex[0:firsthour_end],
                          samples[0:firsthour_end])
                savecheck(path_ext, filename_ext,
                          tindex[secondhour_start:],
                          samples[secondhour_start:])
            else:
                save_to_hour_file(path, filename,
                                  tindex[0:firsthour_end],
                                  samples[0:firsthour_end])
                save_to_hour_file(path_ext, filename_ext,
                                  tindex[secondhour_start:],
                                  samples[secondhour_start:])

        if args.delete_files:
            if args.dry_run:
                print("Would remove"+myfiles[i])
            else:
                os.remove(myfiles[i])
                logging.debug("\t - removed " + myfiles[i])
        if args.dry_run:
            print("--")  # Just to provide a nicer output format...


if __name__ == "__main__":
    main()
