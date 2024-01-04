#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan  4 11:30:11 2024

@author: mikko

The streaming of IQ-data from the USRP does not always work perfectly
and there are small random gaps in data. The missing IQ-samples are
often replaced with zeros in software radio setups. It would be better to do 
this at the higher sampling rate (200kHz with N200's) but this is probably
something that requires switching from python to C in order to do it in realtime.
Something to figure out later...

This short script reads in raw data in npz-format, extents the time range
to cover a full hour and then inter/extrapolates new IQ-values to a perfect
nominal temporal resolution as if no samples were missed.

The input file is expected to be a numpy save file that covers up to one hour
of data. The output file covers a full hour of data with all missing samples
being filled with zeros. 

"""

import numpy as np
import argparse
import datetime as dt
import pytz
from scipy import interpolate
import os
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Test spectrogram")
    parser.add_argument("-i", "--input-file", type=str,
                        required=True, help="Input file (NumPy data)")

    return parser.parse_args()


def main(filelist):
    for filename in filelist:
        print(filename)        
        mydata = np.load(filename)
        ts = mydata["timestamps"]
        iq = mydata["iq"]
        
        # Sort the incoming data based on the timestamps
        ind = np.argsort(ts)
        ts_sorted = ts[ind]
        iq_sorted = iq[ind]
        
        utctz=pytz.timezone(('UTC')) # To avoid weird things..
        
        ts_min=np.min(ts_sorted)
        ts_max=np.max(ts_sorted)
        
        data_start=dt.datetime.fromtimestamp(ts_min,tz=utctz)
        data_end=dt.datetime.fromtimestamp(ts_max,tz=utctz)
        
        if data_end-data_start>dt.timedelta(hours=1):
            print('The data covers more than one hour, which should not happen!')
            print('Exiting...')
            exit()
        
        newdata_start=data_start.replace(minute=0,second=0,microsecond=0)
        newdata_end=newdata_start+dt.timedelta(hours=1)    
        newts_min=newdata_start.timestamp()
        newts_max=newdata_end.timestamp()
            
        print('\t',newdata_start,'\t',newdata_end)
    
        # The nominal sampling frequency is 100Hz
        # - form a "perfect" timestamp vector
        # - inter/extrapolate new complex sample values
        # - fill missing sample instants with "zeros"
        fs=100
        delta_t=1/fs
        new_ts=np.arange(newts_min,newts_max,step=delta_t)
        f=interpolate.interp1d(ts_sorted,iq_sorted,fill_value=0, bounds_error=False)
        new_iq=f(new_ts)
       
        # Store the interpolated data with a slightly modified name
        # into the same directory as the original file
        outpath=os.path.split(filename)[0]
        newname=os.path.splitext(filename)[0]+'-nogaps.npz'
        outfile=os.path.join(outpath,newname)
        print('\t -> ', outfile)
        np.savez(outfile,timestamps=new_ts,iq=new_iq)
    

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("fillDataGaps.py {filename.npz} [filename2.npz] [...]")
        sys.exit()
    main(sys.argv[1:])
    