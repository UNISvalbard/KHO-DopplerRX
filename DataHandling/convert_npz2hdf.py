#!/usr/bin/env python3
"""
Convert individual npz-datafiles to HDF5-format and add relevant
metadata.

"""

import numpy as np
import h5py
import argparse
# import glob
# import os
import datetime as dt
import logging
# import pathlib


def parse_args():
    """ Either use defaults or get something from the user"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    # parser.add_argument("-d", "--delete-files", action="store_true")
    #    parser.add_argument("-i", "--input-file", required=True)
    # parser.add_argument("-o", "--output-directory",
    #                    default="/dev/shm/Doppler")
    parser.add_argument("-i", "--input-file",
                        default="/home/mikko/hdftests/tst.npz")
    parser.add_argument("-o", "--output-directory",
                        default="/home/mikko/hdftests")

    return parser.parse_args()


def savetoHDF5(filename):
    mydata = np.load(filename)
    ts = mydata["timestamps"]
    iqdata = mydata["iq"]

    # Sort the data into sequential order
    i = np.argsort(ts)
    ts = ts[i]
    iqdata = iqdata[i]

    starttime = dt.datetime.utcfromtimestamp(min(ts))
    stoptime = dt.datetime.utcfromtimestamp(max(ts))
    print("File:      ", filename)
    print("Data start:", starttime)
    print("     stop: ", stoptime)
    print("Timestamps:", ts.shape)
    print("   IQ data:", iqdata.shape)

    with h5py.File("/home/mikko/hdftests/testfile.hdf5", "w") as f:
        dset = f.create_dataset("timestamps", data=ts, compression="gzip")
        dset.attrs["Description"] = np.string_(
            "UNIX Time Stamp for each sample")

        dset = f.create_dataset("IQ", data=iqdata, compression="gzip")
        dset.attrs["Description"] = np.string_("Individual samples")

        dset = f.create_dataset("Station", data=h5py.Empty("f"))
        dset.attrs["Name"] = np.string_("Longyearbyen")
        dset.attrs["Institute"] = np.string_("University Centre in Svalbard")
        dset.attrs["Location"] = np.string_("Kjell Henriksen Observatory")
        dset.attrs["Receiver"] = np.string_("78.14798N 16.04235E")
        dset.attrs["Transmitter"] = np.string_("77.00145N 15.54021E")


def main():
    """ Process all individual datafiles into one-hour-files"""
    args = parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Verbose mode")
    savetoHDF5(args.input_file)


if __name__ == "__main__":
    main()
