"""
Created by Olivier on 2026/05/11

A quick script to execute netcdf-metadata.py in a for loop, to convert all the data available 
"""

import configparser
import argparse
from pathlib import Path
import datetime as dt
import subprocess
import sys

config = configparser.ConfigParser()
config.read("config.ini")
raw_data_folder = Path(config['netcdf-metadata-settings']['raw_data_folder'])
destination_folder = Path(config['netcdf-metadata-settings']['destination_folder'])

# Filter to specific dates
# If filter is only applied to 'day', all days with the given number from every year and month will be converted
# Same for months
# For instance, parsing the flag '-m=12' will convert every day from every december
parser = argparse.ArgumentParser(description="hdf5 to netcdf batch files converter")
parser.add_argument("-y", "--year", default='-1', help='Filter for only converting data from the given year')
parser.add_argument("-m", "--month", default='-1', help='Filter for only converting data from the given month')
parser.add_argument("-d", "--day", default='-1', help='Filter for only converting data from the given day')
args = parser.parse_args()

year_filter = int(args.year)
month_filter = int(args.month)
day_filter = int(args.day)


for subfolder in list(raw_data_folder.glob('*/*/*/')) :
    year, month, day = subfolder.parts[-3:]
    date = dt.datetime(year=int(year), month=int(month), day=int(day))

    # Check if a filter was given and if the date corresponds
    if year_filter > 0 and year_filter != date.year :
        continue
    elif month_filter > 0 and month_filter != date.month :
        continue
    elif day_filter > 0 and day_filter != date.day :
        continue
    
    # Execute the converting process for this date
    try :
        subprocess.run([sys.executable, 'netcdf-metadata.py', f'-d={date.strftime('%Y/%m/%d')}'], check=True)
        print(f'Files from {date.strftime('%Y/%m/%d')} successfully converted.')
    except subprocess.CalledProcessError as err :
        print(f'Error while converting files from {date.strftime('%Y/%m/%d')}.')
        print(err)