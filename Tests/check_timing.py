#!/usr/bin/env python3

"""
Checking the timing of recorded data

Each datafile comprises data from one minute. There is a start timestamp
and the last sample time can be computed from the timestamp and the
sampling frequency.

For the Doppler system, fs=100Hz, which means that if the time difference
between the last sample in the current file and the first sample in the next
file is close to 1/100Hz=10ms, then the streaming works correctly
"""

import datetime as dt
import numpy as np
import os.path as opath
import glob


def checkstartstop(fname):
    """Determine the time for the first and the last sample"""
    # fname="testdata2/doppler2020-07-13T23:11:27.npz"
    fdata = np.load(fname)
    starttime = dt.datetime.fromtimestamp(fdata['timestamp'])
    fs = fdata['fs']
    delta = dt.timedelta(seconds=1/fs)
    x = fdata['samples']
    # print(x.size)
    stoptime = starttime+(x.size-1)*delta
    # print(opath.basename(fname),starttime,stoptime)
    return starttime, stoptime


# fname="testdata2/doppler2020-07-13T20:21:24.npz"
# checkstartstop(fname)

myfiles = glob.glob("testdata2/doppler2020-07-14*.npz")
myfiles.sort()
# myfiles=["testdata2/doppler2020-07-14T06:36:27.npz",
#        "testdata2/doppler2020-07-14T06:37:26.npz"]

for i in range(len(myfiles)-1):
    start1, stop1 = checkstartstop(myfiles[i])
    start2, stop2 = checkstartstop(myfiles[i+1])
    # print(start1,"  ",stop2,"   ",start1-stop2)
    # print(start2,"  ",stop1,"   ",start2-stop1)
    # print(opath.basename(myfiles[i+1]),start2,stop2)
    # print(start2-stop1)
    timedifference = start2-stop1
    if timedifference != dt.timedelta(seconds=1/100):
        print(opath.basename(myfiles[i]), opath.basename(myfiles[i+1]),
              timedifference)
