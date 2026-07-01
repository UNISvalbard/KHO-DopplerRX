"""
Created on Thu June 26

@author: Olivier

This script is based on existing code found in spectrogram_netcdf.py and from the open source code
found on http://gwave.cei.uec.ac.jp/~hfd/index.html from the Japanese HF Doppler sounding experiment.

Default comportment :
This script takes in a raw bin file and creates a spectrogram.
This results in a time series which is then refined and plotted.

depending on the value of program_type, the plotting will be done using the japanese code
or the code fount in spectrogram_netcdf.py

Flags :
python spectrogram_japan.py YYYY MM DD 5 AWJ
where YYYY MM DD is year month day
"""

#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as ss
import sys
import glob
import re
import os
import matplotlib.dates as mdates
from matplotlib.cm import ScalarMappable
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.colors as colors
from pylab import *
from struct import *
from pathlib import Path
import datetime as dt

# Base data directory
datadir=Path(r"C:\Users\Olivier\Documents\Polytechnique\3a\Stage\UNIS\PRIDE_radar_data\japanese_data")

program_type = 'svalbard' # 'japan' or 'svalbard'

#--------------------------------------------------------------------------------------------------
# Command line parameters
#--------------------------------------------------------------------------------------------------

args=sys.argv

dyear    = int(args[1])
dmon     = int(args[2])
dday     = int(args[3])
freqnum  = int(args[4])
sta_code = args[5]

if dyear < 2001 :
	print("please input year (> 2001)")
	sys.exit()
if dmon < 1 or dmon > 12 :
	print("please input month (1 to 12)")
	sys.exit()
if dday < 1 or dday > 31 :
	print("please input day (1 to 31)")
	sys.exit()

if freqnum == 5:
	carrier = 0
elif freqnum == 8:
	carrier = 1
elif freqnum == 6:
	carrier = 2
elif freqnum == 9:
	carrier = 3
else:
	print("please input frequency in MHz (5, 6, 8, 9)")
	sys.exit()

# labels of frequencies
flabel  = [5, 8, 6, 9]
f4label = [5006, 8006, 6055, 9595]

#--------------------------------------------------------------------------------------------------
# Basic parameters for digital data
#--------------------------------------------------------------------------------------------------

td = 86400             # the seconds in a day
tsamp = 10             # temporal resolution of data in seconds
timenum=int(td/tsamp)

# Parameters for doing FFT

# Freq range from -4 Hz to 4 Hz
fstart = 2048-164  # -4.0 Hz
fend   = 2048+165  # +4.0 Hz
fsize=fend-fstart  # Frequency range
ylimit = [-4,4]

# FFT size and sampling rate (100 Hz)
fftsize=4096
delta_t=0.01
fs=1/delta_t

#--------------------------------------------------------------------------------------------------
# Reading and processing of digital data
#--------------------------------------------------------------------------------------------------

# File names for the three consecutive days
ddate=datetime.date(dyear,dmon,dday)
ndate=ddate+datetime.timedelta(days=1)
pdate=ddate-datetime.timedelta(days=1)
dgl_cfname=datadir/Path("DGL/"+sta_code+"/bin/{0:04}/".format(ddate.year)+"{0:04}{1:02}{2:02}*_{3:4}_DGL.bin".format(ddate.year,ddate.month,ddate.day,f4label[carrier]))
dgl_pfname=datadir/Path("DGL/"+sta_code+"/bin/{0:04}/".format(pdate.year)+"{0:04}{1:02}{2:02}*_{3:4}_DGL.bin".format(pdate.year,pdate.month,pdate.day,f4label[carrier]))
dgl_nfname=datadir/Path("DGL/"+sta_code+"/bin/{0:04}/".format(ndate.year)+"{0:04}{1:02}{2:02}*_{3:4}_DGL.bin".format(ndate.year,ndate.month,ndate.day,f4label[carrier]))
dgl_cfile=sorted(glob.glob(str(dgl_cfname)))
dgl_pfile=sorted(glob.glob(str(dgl_pfname)))
dgl_nfile=sorted(glob.glob(str(dgl_nfname)))

# Arrays for storing the digital data (for three consecutive days)
dgl_data = [1+1j]*timenum*100*tsamp*3  # Raw intensity data (only the size of this array is 86400 * 3)
dgl_avil = [0]*timenum*100*tsamp*3     # Data availability (if data exist the value is 1, otherwise 0)
dgl_dopf = [99]*(timenum+1)            # Doppler frequency
dgl_ampl = [0]*(timenum+1)             # Intensity at the Doppler frequency

dgl_freqbuf    = np.zeros(fsize)
dgl_afftbuf    = np.zeros(fsize)
dgl_spec       = np.full((fsize,timenum+1),150) # Array for storing dynamic spectra
dgl_freq       = np.fft.fftfreq(fftsize,delta_t)     # Frequency grid of FFT
dgl_freq_shift = np.fft.fftshift(dgl_freq)      # Frequency grid of FFT
dgl_freqbuf[:] = dgl_freq_shift[fstart:fend]

#-----
# Read .bin files on the previous day
#-----
for ifile in range(len(dgl_pfile)):
	filename = Path(dgl_pfile[ifile]).name

	# Get start time 
	# from the filename
	start_time = dt.datetime.strptime(filename[:15], "%Y%m%d_%H%M%S").time()
	delaysec = start_time.hour*3600 + start_time.minute*60 + start_time.second

	dgl_raw=np.fromfile(open(dgl_pfile[ifile]),dtype=np.float32)
	for i in range(len(dgl_raw)//2):
		dgl_data[delaysec*100+i]=complex(dgl_raw[2*i],dgl_raw[2*i+1])
		dgl_avil[delaysec*100+i]=1

#-----
# Read .bin files on the central day
#-----
for ifile in range(len(dgl_cfile)):	
	filename = Path(dgl_cfile[ifile]).name

	# Get start time 
	# from the filename
	start_time = dt.datetime.strptime(filename[:15], "%Y%m%d_%H%M%S").time()
	delaysec = start_time.hour*3600 + start_time.minute*60 + start_time.second

	dgl_raw=np.fromfile(open(dgl_cfile[ifile]),dtype=np.float32)
	for i in range(len(dgl_raw)//2):
		dgl_data[td*100+delaysec*100+i]=complex(dgl_raw[2*i],dgl_raw[2*i+1])
		dgl_avil[td*100+delaysec*100+i]=1

	day_start = td*100+delaysec*100
	day_end = td*100+delaysec*100+len(dgl_raw)//2-1

#-----
# Read .bin files on the next day
#-----
for ifile in range(len(dgl_nfile)):
	filename = Path(dgl_nfile[ifile]).name

	# Get start time 
	# from the filename
	start_time = dt.datetime.strptime(filename[:15], "%Y%m%d_%H%M%S").time()
	delaysec = start_time.hour*3600 + start_time.minute*60 + start_time.second

	dgl_raw=np.fromfile(open(dgl_nfile[ifile]),dtype=np.float32)
	for i in range(len(dgl_raw)//2):
		dgl_data[2*td*100+delaysec*100+i]=complex(dgl_raw[2*i],dgl_raw[2*i+1])
		dgl_avil[2*td*100+delaysec*100+i]=1


if program_type == 'japan' :

	#-----
	# Apply FFT to the entire raw data
	#-----
	for i in range(int(td/tsamp+1)):
		snum=int(td*100+i*tsamp*100-fftsize/2)
		enum=int(snum+fftsize)
		dbuf=dgl_data[snum:enum]
		abuf=dgl_avil[snum:enum]
		if np.count_nonzero(abuf)==fftsize:
			fwindow=np.hamming(len(dbuf))
			fftbuf=np.fft.fft(fwindow*dbuf)
			fftbuf=np.fft.fftshift(fftbuf)
			dgl_afftbuf=20*np.log10(np.abs(fftbuf[fstart:fend]))
			dgl_spec[0:fsize,i]=dgl_afftbuf[0:fsize]
			dgl_dopf[i]=dgl_freqbuf[np.argmax(dgl_afftbuf)]
			dgl_ampl[i]=np.max(dgl_afftbuf)
			hh=int(i*10/3600)
			mm=int((i*10-hh*3600)/60)
			ssecond=int(i*10-hh*3600-mm*60)


	#---------------------------------
	# Plotting data part
	#---------------------------------

	fig,axes=plt.subplots(3,1,figsize=(8.27,11.69))
	fig.subplots_adjust(hspace=0.0)

	nt=6
	timetick=['00', '04', '08', '12', '16', '20', '24']
	inittime=datetime.datetime(dyear,dmon,dday,0,0,0,0)
	xlabelpos=list(range(0,timenum+1,int(timenum/(nt))))

	x=np.arange(timenum+1)
	y=dgl_freqbuf
	xx,yy=np.meshgrid(x, y)

	# 0th panel
	axes[0].margins(0.0)
	axes[0].set_xlim(0,timenum)
	axes[0].set_xlabel("")
	axes[0].set_xticks([])
	axes[0].set_ylabel("Delta f (Hz)")
	axes[0].set_ylim(ylimit[0],ylimit[1])
	axes[0].set_yticks([-2.0, 0, 2.0, 4.0])
	axes[0].set_yticks([-4.0, -3.5, -3.0, -2.5, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5], minor=True)
	spectl_masked = np.ma.masked_where(dgl_spec>100,dgl_spec)
	pcm=axes[0].pcolormesh(xx,yy,spectl_masked,cmap='jet',vmin=-50,vmax=50)
	axes[0].plot([0,timenum],[0,0],linewidth=1,color='white')
	axes[0].plot([0,timenum],[0,0],linewidth=1,linestyle='dotted',color='black')
	ax_cb=plt.axes([0.91,0.6234,0.01,0.88-0.6234]) #the new axis for first colorbar
	cb=plt.colorbar(pcm,cax=ax_cb,orientation='vertical')
	cb.set_label('dB',rotation=270,labelpad=10)

	# 1st panel (Amplitude)
	axes[1].margins(1)
	axes[1].set_xlim(0,timenum)
	axes[1].set_xlabel("")
	axes[1].set_xticks([])
	axes[1].set_ylabel("Amplitude (dB)")
	axes[1].set_ylim(-40,60)
	axes[1].scatter(x,dgl_ampl,color='blue',s=1,marker='.')

	# 2nd panel (Doppler frequency)
	axes[2].margins(1)
	axes[2].set_xlim(0,timenum)
	axes[2].set_xlabel("")
	axes[2].set_xticks([])
	axes[2].set_ylabel("Delta f (Hz)")
	axes[2].set_ylim(ylimit[0],ylimit[1])
	axes[2].set_yticks([-4.0,-2.0, 0, 2.0])
	axes[2].set_yticks([-4.0, -3.5, -3.0, -2.5, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5], minor=True)
	axes[2].scatter(x,dgl_dopf,color='blue',s=1,marker='.')
	axes[2].plot([0,timenum],[0,0],linewidth=1,color='white')
	axes[2].plot([0,timenum],[0,0],linewidth=1,linestyle='dashed',color='black')
	axes[2].set_xlabel("Universal Time (UT = JST - 9)")
	axes[2].set_xticks(xlabelpos)
	axes[2].set_xticks([1,2,3], minor=True)
	axes[2].set_xticklabels(timetick)

	#---------------------------
	# Save image file or display
	#---------------------------
	plotfilename='{:04}{:02}{:02}_{:04}kHz.png'.format(dyear,dmon,dday,f4label[carrier])
	plt.rcParams["font.family"]="arial"
	plt.rcParams["xtick.direction"]="in"
	plt.rcParams["ytick.direction"]="in"
	plt.savefig(plotfilename)
	plt.show()





elif program_type == 'svalbard' : 

	start_date = dt.datetime(year=dyear, month=dmon, day=dday)

	# ------------------------------------------------
    # Run spectrogram + extract peaks of the filtered data

	data_dict = {}
	sample_frequency = fs

	# Take only the date from the selected day
	sample_IQ = np.array(dgl_data[day_start:day_end])

	decimated_IQ = ss.decimate(sample_IQ, 10)
	sos = ss.butter(10, 2, btype='low', fs=sample_frequency/10, output='sos')
	filtered_IQ = ss.sosfilt(sos, decimated_IQ)

	STF = ss.ShortTimeFFT.from_window('hann', fs=sample_frequency/10, nperseg=256, noverlap=32, fft_mode='twosided', mfft=4096, scale_to='psd')

	f = STF.f
	data_dict['freq'] = np.array(fftshift(f))

	t = STF.t(len(filtered_IQ))
	data_dict['time'] = np.array(t)

	Sxx = STF.spectrogram(filtered_IQ)
	# Convert to dB and normalize so strongest point is 0 dB
	Syy = 10 * np.log10(Sxx.squeeze())
	Syy = Syy - np.max(Syy)
	data_dict['Syy_shifted'] = np.array(fftshift(Syy, axes=0))

	# Find frequency where max occurs for each time bin
	max_index = np.argmax(Syy, axis=0)
	data_dict['max_freq'] = np.array(f[max_index])


	# ------------------------------------------------
	# Plot the obtained data

	# Unpack data 
	data_dict['timestamps'] = np.array([start_date + dt.timedelta(milliseconds=int(data_dict['time'][k]*1000)) for k in range(len(data_dict['time']))])
	time = data_dict['timestamps']
	frequency = data_dict['freq']
	max_psd = data_dict['max_freq']
	syy = data_dict['Syy_shifted']

	# Spectrogram limits, display downsampling factors
	freq_boundary = 3
	freq_limits = (abs(frequency) <= freq_boundary)
	frequency = frequency[freq_limits]
	syy_limited = syy[freq_limits, :]
	syy_max = np.percentile(syy_limited, 99.5)

	f_ddfactor = 2
	t_ddfactor = 2

	# Avoid using matplotlib.pyplot as it prevents tkinter window from closing
	# Axes definition
	fig = plt.figure(figsize=(15, 5))
	gs = GridSpec(3, 2, figure=fig,height_ratios=[0.45, 0.45, 0.1], width_ratios=[0.99, 0.01])
	ax0 = fig.add_subplot(gs[0]) # ax for spectrogram
	cax0 = fig.add_subplot(gs[1]) # ax for colorbar 
	ax1 = fig.add_subplot(gs[2]) # ax for max_psd
	ax_container = fig.add_subplot(gs[4])
	ax_slider = ax_container.inset_axes((0.1, 0.2, 0.8, 0.6)) # ax for slider
	ax_container.axis('off')
	fig.subplots_adjust(bottom=0.2)

	# Spectrogram plot
	spectrogram = ax0.imshow(syy_limited[::f_ddfactor, ::t_ddfactor], 
								aspect='auto', origin='lower', interpolation='nearest',
								vmin=syy_max-30, vmax=syy_max,
								cmap='viridis')
	ax0.set_title(f'Spectrogram')
	ax0.set_ylabel('Frequency (Hz)')
	colorbar = fig.colorbar(spectrogram, cax=cax0, fraction=0.05, pad=0.01)
	colorbar.set_label('Received power (dB)')

	# Maximum PSD plot
	psd_plot, = ax1.plot(time[::t_ddfactor], max_psd[::t_ddfactor], linestyle='None', marker='+', markersize=4)

	ax1.set_xlim(time[0], time[-1])
	ax1.set_ylim(-freq_boundary, freq_boundary)
	ax1.set_autoscale_on(False)

	ax1.set_title(f"Frequency of Strongest Peak vs Time - filtered and downshifted - {start_date.strftime('%Y/%m/%d')}")
	ax1.set_ylabel("Frequency of Maximum PSD (Hz)")
	ax1.grid(alpha=0.3)

	ax1.set_xlabel("Time")
	ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))


	# Update spectrogram ticks to match that of psd plot
	def update_ticks(axis=0) :
		if axis == 0 :
			N = spectrogram.get_array().shape[1]
			ax0.set_xticks(np.linspace(0, N-1, len(ax1.get_xticks())))
			ax0.set_xticklabels([f'{x:g}' for x in ax1.get_xticks()])
		elif axis == 1 :
			N = spectrogram.get_array().shape[0]
			ax0.set_yticks(np.linspace(0, N-1, len(ax1.get_yticks())))
			ax0.set_yticklabels([f'{x:g}' for x in ax1.get_yticks()])
			
	# update_ticks(axis=0)
	ax0.get_xaxis().set_visible(False)
	update_ticks(axis=1)


	# Slider definition and fig update 
	window_width = dt.timedelta(hours=1)
	slider = Slider(ax=ax_slider, label="Displayed hour", valmin=0, valmax=1, valinit=0)

	def format_time(val) : 
		return time[0] + val * (time[-1] - dt.timedelta(hours=1) - time[0])

	slider.valtext.set_text(f"{format_time(slider.val).strftime('%H:%M')}")


	# Update loop function
	def update(val) :
		start_display = format_time(slider.val)
		end_display = start_display + window_width
		time_filter = (time >= start_display) & (time < end_display)

		# Filter and downsample the displayed data
		spectrogram.set_data(syy_limited[:, time_filter][::f_ddfactor, :])
		psd_plot.set_data(time[time_filter], max_psd[time_filter])

		ax1.set_xlim(start_display, end_display)
		slider.valtext.set_text(f"{start_display.strftime('%H:%M')}")
		# update_ticks(axis=0)
	slider.on_changed(update)


	# Handling function for the mouse wheel
	def on_scroll(event) :
		if event.inaxes == ax_slider or event.inaxes in (ax0, ax1) :
			current_val = slider.val
			step = 0.005
			
			if event.step < 0:
				new_val = min(current_val + step, slider.valmax)
			else:
				new_val = max(current_val - step, slider.valmin)
				
			slider.set_val(new_val)
	fig.canvas.mpl_connect('scroll_event', on_scroll)

	gs.tight_layout(fig)

	plt.show()

