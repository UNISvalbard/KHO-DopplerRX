#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 22 11:03:46 2024

@author: mikko

This script was written during the Data workshop by Luke Marsden (UNIS) on 
Monday, 22 January, 2024.

The code is based on previous python scripts
https://github.com/lhmarsden/cf-netcdf_workshop_nov2023

The data files have been tested with the SIOS compliance checker tool and
the output is compliant with ACDD-1.3. The tool can only check up to 
the CF version 1.8, which does not have the "radiation power" keyword, which
is available in CF version 1.11

To do:
    - find out how to make new CF-NetCDF-files available
"""

import xarray as xr
import numpy as np
import h5py
import configparser
import argparse
from pathlib import Path
import datetime as dt


# ------------------------------------------------
# Read config for testing
config = configparser.ConfigParser()
config.read("config.ini")
data_path = Path(config['visual_tool_settings']['raw_data_folder'])
str_date = config['visual_tool_settings']['date']
destination_path = Path(config['visual_tool_settings']['netcdf_folder'])

parser = argparse.ArgumentParser(description="File converter hdf5 to netcdf with metadata")
parser.add_argument("-d", "--date", default=str_date)
args = parser.parse_args()
str_date = args.date

target_date = dt.datetime.strptime(str_date, '%Y/%m/%d').date()


# ------------------------------------------------
# Import data of the RX signal

# Create a list of filepaths corresponding to all the data created during a given day
day_data_path = data_path / target_date.strftime('%Y/%m/%d')
files_list = list(day_data_path.glob('*-nogaps.hdf5'))

# Ceating a dictionnary for centralizing the data
data_dict = {}
data_dict['timestamps'] = []
data_dict['samples_I'] = []
data_dict['samples_Q'] = [] 

# Fetch, concatenate and roughly format the data
for i in range(24) :
    # Add the data if exists
    file_path = day_data_path / f"doppler_lyr_{target_date.strftime('%Y%m%d')}_{str(i).zfill(2)}UT-nogaps.hdf5"
    if file_path in files_list :
        f = h5py.File(file_path, 'r')

        data_dict['timestamps'].append(f['timestamps'][()].copy())
        data_dict['samples_I'].append(f['IQ'][()].copy().real)
        data_dict['samples_Q'].append(f['IQ'][()].copy().imag)

        f.close()
    
    # else fill the missing hour with timestamped NaN
    else :
        Nsamples = 60*60*100    # 1 hour at 100Hz 
        missing_hour = dt.datetime.combine(target_date, dt.time(hour=i), tzinfo=dt.UTC)

        missing_timestamps = np.arange(Nsamples) * 0.01 + missing_hour.timestamp()
        missing_data = np.full((Nsamples, ), np.nan)

        data_dict['timestamps'].append(missing_timestamps)
        data_dict['samples_I'].append(missing_data)
        data_dict['samples_Q'].append(missing_data)
    

for key in data_dict.keys() :
    data_dict[key] = np.concatenate(data_dict[key], axis=0)

start_timestamp = data_dict['timestamps'][0]
data_dict['ms_since_start'] = (data_dict['timestamps'] - start_timestamp) * 1000
data_dict['ms_since_start'] = data_dict['ms_since_start'].astype(int)


# ------------------------------------------------
# Create xr dataset

# Transmitter details
# - located in at the Polish Polar Station in Hornsund
# - transmits a CW at 4.45MHz

latitude_tx = 77.00145
longitude_tx = 15.54021
tx_frequency = 4450000


# Receiver details
# - locate at the Kjell Henriksen Observatory
# - receiver hardware uses an Ettus software-defined radio, which is
#   essentially a direct conversion receiver
# - receiver tuned 25Hz below the transmit frequency, so that
#   we can avoid the "DC spike" by simply shifting the spectrum

latitude_rx = 78.14798
longitude_rx = 16.04235
rx_frequency = 4450000-25


prideds = xr.Dataset()

prideds = xr.Dataset(
    coords={
        'time': data_dict['ms_since_start'],
        'latitude_tx': latitude_tx,
        'longitude_tx': longitude_tx,
        'latitude_rx': latitude_rx,
        'longitude_rx': longitude_rx,
    }
)

prideds['samples_I'] = ("time", data_dict['samples_I'])
prideds['samples_Q'] = ("time", data_dict['samples_Q'])
prideds['tx_frequency'] = tx_frequency
prideds['rx_frequency'] = rx_frequency


#------------------------------------------------
# Add metadata

start_date = dt.datetime.fromtimestamp(data_dict['timestamps'][0], tz=dt.UTC)
end_date = dt.datetime.fromtimestamp(data_dict['timestamps'][-1], tz=dt.UTC)

prideds['time'].attrs = {
    'standard_name':'time',
    'long_name': 'time',
    'units': f'milliseconds since {start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}',
    'calendar': 'standard',
    'coverage_content_type': 'coordinate'
}

prideds['latitude_tx'].attrs = {
    'standard_name': 'latitude',
    'long_name': 'latitude transmitter',
    'units': 'degrees_north',
    'coverage_content_type': 'coordinate'
}

prideds['longitude_tx'].attrs = {
    'standard_name': 'longitude',
    'long_name': 'longitude transmitter',
    'units': 'degrees_east',
    'coverage_content_type': 'coordinate'
}

prideds['latitude_rx'].attrs = {
    'standard_name': 'latitude',
    'long_name': 'latitude receiver',
    'units': 'degrees_north',
    'coverage_content_type': 'coordinate'
}

prideds['longitude_rx'].attrs = {
    'standard_name': 'longitude',
    'long_name': 'longitude receiver',
    'units': 'degrees_east',
    'coverage_content_type': 'coordinate'
}

prideds['samples_I'].attrs = {
    'long_name': 'In-phase component of the sample',
    'units': '1',
    'coverage_content_type': 'physicalMeasurement'
}

prideds['samples_Q'].attrs = {
    'long_name': 'Quadrature component of the sample',
    'units': '1',
    'coverage_content_type': 'physicalMeasurement'
}


prideds['tx_frequency'].attrs = {
    'standard_name': 'radiation_frequency',
    'long_name': 'Transmit frequency',
    'units': 'Hz',
    'coverage_content_type': 'physicalMeasurement'
}

prideds['rx_frequency'].attrs = {
    'standard_name': 'radiation_frequency',
    'long_name': 'Receive frequency',
    'units': 'Hz',
    'coverage_content_type': 'physicalMeasurement'
}


#------------------------------------------------
# Global attributes

dtnow = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

# Global attributes based on https://adc.met.no/submit-data-as-netcdf-cf
prideds.attrs = {
    'researchinsvalbard_id': '11522',
    'title': 'Polar Research Ionospheric Doppler Experiment',
    # TODO: The summary could be longer. Like an abstract for a paper, describing the data and processing if applicable.
    'summary':  """
                Records of received continuous-wave transmissions at a single frequency bounced reflected by the ionosphere.

                The data contained in this netcdf file consists of a 100 Hz sample of the received signal from the PRIDE radar located on Svalbard
                over the course of 24 hours, decoupled into its I and Q components.
                
                The transmitter emits a 20W continuous carrier wave at 4.45 MHz.
                When the waves reflect back to the receiver, any changes in the ionosphere properties, mainly due to Atmospheric Gravity waves
                and Ultra Low Frequency Magnetohydodynamic waves, contribute to a Doppler shift that can be measured.
                The receiver loop antenna is connected to a software-defined radio via a lowpass filter, and its output is processed as a single I/Q complex signal.
                Initially recorded at a 200 kHz sampling rate callibrated via GNSS time, the I/Q samples are decimated to a 100 Hz sampling rate. 
                Maintenance on the system, power cuts or other factors can sometimes lead to missing samples, which are filled with zeros 
                before the decimation to minimise the impact on the final samples.
                The I and Q components of the signal are decoupled and finally saved separately into this netcdf files along with their timestamp. 
                """,
    'keywords': 'GCMDSK:Earth Science > Sun-Earth interactions > ionosphere-magnetosphere dynamics > plasma waves',
    'keywords_vocabulary': 'GCMDSK:GCMD Science Keywords:https://gcmd.earthdata.nasa.gov/kms/concepts/concept_scheme/sciencekeywords',
    'iso_topic_category': 'climatologyMeteorologyAtmosphere', # Select from here, change or remove if this is not suitable https://wiki.esipfed.org/ISO_Topic_Categories
    'geospatial_lat_min': str(min(latitude_tx,latitude_rx)),
    'geospatial_lat_max': str(max(latitude_tx,latitude_rx)),
    'geospatial_lon_min': str(min(longitude_tx,longitude_rx)),
    'geospatial_lon_max': str(max(longitude_tx,longitude_rx)),
    'time_coverage_start': start_date.strftime('%Y-%m-%dT%H:%M:%S'),
    'time_coverage_end': end_date.strftime('%Y-%m-%dT%H:%M:%S'),
    'Conventions': 'ACDD-1.3, CF-1.11',
    'history': f'File created at {dtnow}',
    'processing_level': 'Missing samples replaced with zeros and resampled',
    'date_created': dtnow,
    'creator_type': 'person',
    'creator_institution': 'University Centre in Svalbard',
    'creator_institution_pid': 'https://ror.org/03cyjf656', 
    'creator_name': 'Mikko Syrjäsuo',
    'creator_email': 'myemailhere@unis.no',
    'creator_url': 'https://www.unis.no/staff/mikko-syrjasuo/',
    'creator_pid': 'https://orcid.org/0000-0002-6113-6855',
    'publisher_type': 'institution',
    'publisher_name': 'Norwegian Meteorological Institute/Arctic Data Centre (NO/MET/ADC)',
    'publisher_email': 'adc-support@met.no',
    'publisher_institution': 'Norwegian Meteorological Institute',
    'publisher_institution_pid': 'https://ror.org/001n36p86',
    'publisher_url': 'https://adc.met.no/',
    'project': 'Kjell Henriksen Observatory (KHO)',
    'license': 'http://spdx.org/licenses/CC-BY-4.0 (CC-BY-4.0)',
    'standard_name_vocabulary': 'CF Standard Name Table v84',
    'comment': 'Raw data available from UNIS',
    # TODO: Fill the below in based on https://adc.met.no/submit-data-as-netcdf-cf#platform
    'instrument': '',
    'instrument_vocabulary': '',
    'project': 'Polar Research Ionospheric Doppler Experiment (PRIDE)'
}


#-----------------------------------------------
# Export to CF-NetCDF

outfile = destination_path / f'test_PRIDE_{target_date.strftime('%Y%m%d')}.nc'

# Specifiy encoding
myencoding = {
    'time': {
        'dtype': 'int64',
        '_FillValue': None  # Coordinate variables should not have fill values.
    },
    'latitude_tx': {
        'dtype': 'float64',
        '_FillValue': None  # Coordinate variables should not have fill values.
    },
    'longitude_tx': {
        'dtype': 'float64',
        '_FillValue': None  # Coordinate variables should not have fill values.
    },
    'latitude_rx': {
        'dtype': 'float64',
        '_FillValue': None  # Coordinate variables should not have fill values.
    },
    'longitude_rx': {
        'dtype': 'float64',
        '_FillValue': None  # Coordinate variables should not have fill values.
    },
    'samples_I': {
        'dtype': 'float64',
        '_FillValue': None
    },
    'samples_Q': {
        'dtype': 'float64',
        '_FillValue': None
    },
    'tx_frequency': {
        'dtype': 'int64'
    },
    'rx_frequency': {
        'dtype': 'int64'
    }
}

prideds.to_netcdf(outfile, encoding=myencoding)
