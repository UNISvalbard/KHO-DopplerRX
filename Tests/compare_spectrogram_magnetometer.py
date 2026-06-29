import numpy as np
import datetime as dt
import xarray as xr
import matplotlib.pyplot as plt
from pathlib import Path
import configparser


# ------------------------------------------------
# Read config and parse args

config = configparser.ConfigParser()
config.read('config.ini')
spectrogram_folder = Path(config['compare_spectrogram']['spectrogram_folder'])
magnetometer_folder = Path(config['compare_spectrogram']['magnetometer_folder'])
str_date = config['spectrogram_netcdf-settings']['date']


date = dt.datetime(year=2023, month=12, day=17, hour=18)
duration = dt.timedelta(hours=2)



# ------------------------------------------------
# Read specrogram

time_series_file = spectrogram_folder / f'test_PRIDE_spectrogram_{date.strftime('%Y%m%d')}.nc'
with xr.open_dataset(time_series_file, decode_cf=False) as timeseries_dataset :
    spectro_dict = {}
    spectro_dict['time'] = np.array(timeseries_dataset['time'])
    spectro_dict['max_freq'] = np.array(timeseries_dataset['max_freq'])

    start_date_str = timeseries_dataset['time'].attrs['units'].split(' ')[2]
    start_date = dt.datetime.fromisoformat(start_date_str)
    spectro_dict['timestamps'] = np.array([start_date.replace(tzinfo=None) + dt.timedelta(seconds=int(spectro_dict['time'][k])) for k in range(len(spectro_dict['time']))])

spectro_date_filter = (spectro_dict['timestamps'] >= date) & (spectro_dict['timestamps'] < date + duration)

for key in spectro_dict.keys() :
    spectro_dict[key] = spectro_dict[key][spectro_date_filter]

# ------------------------------------------------
# Read magnetometer data

magnetometer_file = magnetometer_folder / f'image_{date.strftime('%Y%m%d')}.txt'
with open(magnetometer_file, 'r') as file:
    magneto_dict = {'time':[],
                    'Bx':[],
                    'By':[]}
    
    next(file)
    next(file)
    
    for line in file:
        content = line.split()
        magneto_date = dt.datetime(year=int(content[0]),
                                   month=int(content[1]),
                                   day=int(content[2]),
                                   hour=int(content[3]),
                                   minute=int(content[4]),
                                   second=int(content[5]))
        if date <= magneto_date and magneto_date < date + duration: 
            magneto_dict['time'].append(magneto_date)
            # In order: NAL, LYR, HOR
            magneto_dict['Bx'].append(np.array([float(content[6]), float(content[9]), float(content[12])]))
            magneto_dict['By'].append(np.array([float(content[7]), float(content[10]), float(content[13])]))

    for key in magneto_dict.keys() :
        magneto_dict[key] = np.array(magneto_dict[key])



# ------------------------------------------------
# Create the fft

dt_spectro = np.mean(np.diff(spectro_dict['timestamps'])).total_seconds()
dt_magneto = np.mean(np.diff(magneto_dict['time'])).total_seconds()

fft_spectro = np.fft.rfft(spectro_dict['max_freq'])
freq_spectro = np.fft.rfftfreq(len(spectro_dict['max_freq']), d=dt_spectro)
norm_spectro = 2 * np.abs(fft_spectro) / len(spectro_dict['timestamps'])

station_list = ['NÅL', 'LYR', 'HOR']
station = 1

fft_magneto_x = np.fft.rfft(magneto_dict['Bx'][:, station])
freq_magneto_x = np.fft.rfftfreq(len(magneto_dict['Bx'][:, station]), d=dt_magneto)
norm_magneto_x = 2* np.abs(fft_magneto_x) / len(magneto_dict['Bx'][:, station])

fft_magneto_y = np.fft.rfft(magneto_dict['By'][:, station])
freq_magneto_y = np.fft.rfftfreq(len(magneto_dict['By'][:, station]), d=dt_magneto)
norm_magneto_y = 2* np.abs(fft_magneto_y) / len(magneto_dict['By'][:, station])

def low_filter(freq_data, norm_data, min_freq):
    filter_data = (freq_data > min_freq)
    return (freq_data[filter_data], norm_data[filter_data])

min_freq = 0.0001

# freq_spectro, norm_spectro = low_filter(freq_spectro, norm_spectro, min_freq)
# freq_magneto_x, norm_magneto_x = low_filter(freq_magneto_x, norm_magneto_x, min_freq)
# freq_magneto_y, norm_magneto_y = low_filter(freq_magneto_y, norm_magneto_y, min_freq)

plt.figure(figsize=(10, 5))

plt.plot(freq_spectro, norm_spectro, label='PRIDE PSD', alpha=0.8, lw=1, c='b')
plt.plot(freq_magneto_x, norm_magneto_x, label=f'{station_list[station]} B_x', alpha=0.5, lw=1, ls='--', c='lightcoral')
plt.plot(freq_magneto_y, norm_magneto_y, label=f'{station_list[station]} B_y', alpha=0.5, lw=1, ls=':', c='seagreen')


plt.xlabel("Frequency (Hz)")
plt.ylabel("Amplitude")
plt.legend()
plt.grid(True)
plt.xlim(0, 0.01)
plt.ylim(0, 3)
plt.title(f'{date.strftime('%Y/%m/%d')}')
plt.show()