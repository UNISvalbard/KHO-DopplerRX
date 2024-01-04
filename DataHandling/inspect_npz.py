#!/usr/bin/env python3

"""
A quick script to check what one or more npz-files contain.
Essentially prints out the array names and the array sizes in each npz-file
"""

import sys
import numpy as np
import datetime as dt
import pytz

utctz=pytz.timezone('UTC')
if len(sys.argv) == 1:
    print("inspect_npz.py {filename.npz} [filename2.npz] [...]")
    sys.exit()
    
for thisfile in sys.argv[1:]:
    print(thisfile)
    try:
        a = np.load(thisfile)
        for i in a.files:
            print("\t", i, a[i].shape)
        ts_min=np.min(a['timestamps'])
        ts_max=np.max(a['timestamps'])
        data_start=dt.datetime.fromtimestamp(ts_min,tz=utctz)
        data_end=dt.datetime.fromtimestamp(ts_max,tz=utctz)
        print('\tFrom:',data_start)
        print('\tTo:  ',data_end)
    except FileNotFoundError:
        print("\tFile not found!")
    except ValueError:
        print("\tBad npz-file?")
