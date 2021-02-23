#!/usr/bin/env python3

"""
A quick script to check what one or more npz-files contain.
Essentially prints out the array names and the array sizes in each npz-file
"""

import sys
import numpy as np

if len(sys.argv) == 1:
    print("inspect_npz.py {filename.npz} [filename2.npz] [...]")
    sys.exit()
for thisfile in sys.argv[1:]:
    print(thisfile)
    try:
        a = np.load(thisfile)
        for i in a.files:
            print("\t", i, a[i].shape)
    except FileNotFoundError:
        print("\tFile not found!")
    except ValueError:
        print("\tBad npz-file?")
