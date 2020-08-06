# Data handling routines

## Basic philosophy

From the end-user's point of view, the data needs to be easy to use and one should be able to import data to the preferred platform (python, Matlab etc.) without too many difficulties. The goal is to have HDF5-formatted files with relevant metadata. Each file should not be too large and storing one hour of data in one file provides reasonable flexibility in practice

## Data flow

The script that streams recorded RF data (baseband) to disk saves small one-minute files in NumPy binary format using ```np.savez()```. These small files are then merged into appropriate one-hour numpy binary files. The files contain two vectors (```numpy.ndarray```) for unix-style timestamps and for the IQ-data (complex baseband).

## Conversion from numpy to HDF5

The HDF5 file thus contains IQ-samples with timestamps, which are based on GPS reference time. However, while the time between the samples is nominally 10ms (1/Fs, where Fs=100Hz), the sampling instants do not align with "zero seconds" perfectly. To simplify the data analysis, the data in the HDF5 files should probably be resampled/interpolated to the nominal sampling grid.

## TODO
* Improved data handling to avoid duplicate samples
* Resampling/interpolation of samples to obtain a constant fixed grid. Possibly better to have a separate routine to do this to maintain the original data, maybe an option to use when reading the data for analysis?
