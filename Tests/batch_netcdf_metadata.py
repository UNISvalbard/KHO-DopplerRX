"""
Created by Olivier on 2026/05/11

A quick script to execute netcdf-metadata.py in a for loop, to convert all the data available 
"""

import configparser
from pathlib import Path
import datetime as dt
import subprocess
import sys

config = configparser.ConfigParser()
config.read("config.ini")
raw_data_folder = Path(config['netcdf-metadata-settings']['raw_data_folder'])
destination_folder = Path(config['netcdf-metadata-settings']['destination_folder'])

for subfolder in list(raw_data_folder.glob('*/*/*/')) :
    year, month, day = subfolder.parts[-3:]
    date = dt.datetime(year=int(year), month=int(month), day=int(day))
    try :
        subprocess.run([sys.executable, 'netcdf-metadata.py', f'-d={date.strftime('%Y/%m/%d')}'], check=True)
        print(f'Files from {date.strftime('%Y/%m/%d')} successfully converted.')
    except subprocess.CalledProcessError as err :
        print(f'Error while converting files from {date.strftime('%Y/%m/%d')}.')
        print(err)