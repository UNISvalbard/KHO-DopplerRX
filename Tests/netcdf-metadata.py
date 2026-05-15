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
    - read real data...
    - decide on filenaming conventions
    - find out how to make new CF-NetCDF-files available

"""

import xarray as xr
import numpy as np
from datetime import datetime as dt

Nsamples = 60*100 # One minute at 100Hz

# Complex samples of RX signal
# - replace with real data at some point...

samples_I = np.random.randn(Nsamples)
samples_Q = np.random.randn(Nsamples)


# Timestamps for the IQ samples sampled at 100Hz (dt=10ms)

start = np.datetime64('2024-01-22T00:00:00')
milliseconds_since_start = 10*np.arange(0, Nsamples).astype('int')
end = start+(Nsamples-1)*np.timedelta64(10,'ms')

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
        'time': milliseconds_since_start,
        'latitude_tx': latitude_tx,
        'longitude_tx': longitude_tx,
        'latitude_rx': latitude_rx,
        'longitude_rx': longitude_rx,
    }
)

prideds['samples_I'] = ("time", samples_I)
prideds['samples_Q'] = ("time", samples_Q)
prideds['tx_frequency'] = tx_frequency
prideds['rx_frequency'] = rx_frequency

#------------------------------------------------
# Add metadata

startdatestr = np.datetime_as_string(start, timezone='UTC')
enddatestr = np.datetime_as_string(end, timezone='UTC')

prideds['time'].attrs = {
    'standard_name':'time',
    'long_name': 'time',
    'units': f'milliseconds since {startdatestr}',
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

dtnow = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

# Global attributes based on https://adc.met.no/submit-data-as-netcdf-cf
prideds.attrs = {
    'researchinsvalbard_id': '11522',
    'title': 'Polar Research Ionospheric Doppler Experiment',
    # TODO: The summary could be longer. Like an abstract for a paper, describing the data and processing if applicable.
    'summary': 'Records of received continuous-wave transmissions at a single frequency bounced reflected by the ionosphere',
    'keywords': 'GCMDSK:Earth Science > Sun-Earth interactions > ionosphere-magnetosphere dynamics > plasma waves',
    'keywords_vocabulary': 'GCMDSK:GCMD Science Keywords:https://gcmd.earthdata.nasa.gov/kms/concepts/concept_scheme/sciencekeywords',
    'iso_topic_category': 'climatologyMeteorologyAtmosphere', # Select from here, change or remove if this is not suitable https://wiki.esipfed.org/ISO_Topic_Categories
    'geospatial_lat_min': str(min(latitude_tx,latitude_rx)),
    'geospatial_lat_max': str(max(latitude_tx,latitude_rx)),
    'geospatial_lon_min': str(min(longitude_tx,longitude_rx)),
    'geospatial_lon_max': str(max(longitude_tx,longitude_rx)),
    'time_coverage_start': startdatestr,
    'time_coverage_end': enddatestr,
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
    'instrument_vocabulary': '' 
}

#-----------------------------------------------
# Export to CF-NetCDF

outfile = 'test5.nc'

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
