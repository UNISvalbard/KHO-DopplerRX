#!/bin/bash

# Processing of individual files with streamed data
#
# Much of the "temporary" data is in /dev/shm so there needs to be
# a regular synchronisation to the actual data area. This script is intended
# to be run from crontab (check the path for the python-script)
#
#
# - move files older than one hour to a staging directory
# - combine the files into one-hour-files
# - add to the main data

# TODO
# - there is a lot of back and forth reading when merging files, so this
#   might be better to do in /dev/shm although one would expect that a modern
#   operating system mostly uses the cache anyway


RAWFILES="/dev/shm"
STAGEDIR="/dev/shm/doppler1h"
DESTDIR="/dev/shm/Doppler"

mkdir -p $STAGEDIR
find $RAWFILES -maxdepth 1 -mmin +65 -name '*.npz' -exec mv {} $STAGEDIR \;
python combine_rawdatafiles.py -i $STAGEDIR -o $DESTDIR -d
