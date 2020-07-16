# Data handling routines

## Basic philosophy

From the end-user's point of view, the data needs to be easy to use and one should be able to import data to the preferred platform (python, Matlab etc.) without too many difficulties. The goal is to have HDF5-formatted files with relevant metadata. Each file should not be too large and storing one hour of data in one file provides reasonable flexibility in practice

## Data flow

The script that records RF saves small one-minute files in numpy binary format using ```np.savez()```. These small files are then merged into appropriate one-hour numpy binary files. The files contain to vectors (```numpy.ndarray``) for unix-style timestamps and for the IQ-data (complex baseband).

## Conversion from numpy to HDF5

The sampling frequency is 100Hz, which is referenced to a GPS time. However, while the time between the samples is nominally 10ms (1/Fs), the instants do not align with "zero seconds" percetly. To simplify the data analysis, the data in the HDF5 files is resampled/interpolated to the nominal sampling grid.

## TODO
* Proper pipeline for data including pruning of data that is already merged
* HDF5 handling including resampling/interpolation
