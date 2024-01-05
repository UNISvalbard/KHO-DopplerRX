filename='doppler_lyr_20231214_15UT-nogaps.hdf5'

% Use h5disp(filename) to see more details about contents
% of the HDF5-file. Note: you'll need the names for the datasets
% in order to read the stored data...

timestamps=h5read(filename,'/timestamps');
iq=h5read(filename,'/IQ');
sampleIQ=iq.r+1j*iq.i; % Convert to a complex-valued samples

dt=datetime(timestamps,'ConvertFrom','posix', ...
    'timezone','utc');
dt.Format='yyyy-MM-dd HH:mm:ss.SSS'; % Show fractional seconds

fprintf('Data from %s to %s\n',min(dt),max(dt))

% Note that the RX frequency is 25Hz below the TX frequency
% -> the signal from Hornsund should appear at 25Hz
% This is a common trick to avoid the large DC component (at 0Hz)
% which you'll see if you don't provide any frequency limits...

fs=1/(timestamps(2)-timestamps(1)); % This should be 100Hz

subplot(1,2,1)
pspectrum(sampleIQ,fs,'spectrogram')

% Processing of the RX signal should include complex mixing
% to shift the spectrum 25Hz down in frequency followed by an
% appropriate lowpass filter to get rid of frequencies we are not
% interested in as well as to reduce noise.

f_LO=-25; % The LO frequency
y_LO=exp(1j*2*pi*f_LO*timestamps);

mixedIQ=sampleIQ.*y_LO; % Complex mixing
filteredIQ=lowpass(mixedIQ,20,fs); % Limit the baseband by filtering

subplot(1,2,2)
pspectrum(filteredIQ,fs,'spectrogram') %,'FrequencyLimits',[-10 10])
