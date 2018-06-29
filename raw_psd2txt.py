"""
Short script for computing and saving PSDs

Takes paths to data files as arguments:
1) file before treatment
2) file after treatment

Saves the PSDs as psd_ceameg.txt, where rows are:
1. mean amplitude spectrum over channels before
2. mean amplitude spectrum over channels after
3. the frequencies

If requested, saves channel-wise spectra before and after in separate files:
ch_psds_<filename_before>.txt
ch_psds_<filename_after>.txt
Also plots mean spectra.

sipemont 180401
"""

save_txts=False;
tmin=0 # begin time reading file
tmax=None # end time reading file
fmin=5 # lowest frequency in spectrum
fmax=30 # highest frequency in spectrum
meg='grad' # 'mag' or 'grad' -- use MAG or GRAD sensors
ch_selection=['Left-frontal'] # 'Right-occipital' or Left-parietal, Right-parietal, etc. -- select the region of interest

import matplotlib
matplotlib.use('qt4agg')
from mne import pick_channels
from mne import read_selection
from mne import pick_channels
import matplotlib.pyplot as plt
import mne.time_frequency as tf
import mne.io as io
import sys
import numpy as np
import os.path as pth
plt.ioff()

fname_B=sys.argv[1]
fname_A=sys.argv[2]

Raw_B=io.read_raw_fif(fname_B, preload=True)
Raw_A=io.read_raw_fif(fname_A, preload=True)

sel=read_selection(ch_selection, info=Raw_B.info)
Raw_B.pick_channels(sel)
sel=read_selection(ch_selection, info=Raw_A.info)
Raw_A.pick_channels(sel)
Raw_B.pick_types(meg=meg)
Raw_A.pick_types(meg=meg)

fsA=int(Raw_A.info['sfreq'])
fsB=int(Raw_B.info['sfreq'])
psd_B, freqs = tf.psd_welch(Raw_B, tmin=tmin, tmax=tmax, fmin=fmin, fmax=fmax, proj=False, n_fft=4*fsB, n_overlap=2*fsB)
psd_A, freqs = tf.psd_welch(Raw_A, tmin=tmin, tmax=tmax, fmin=fmin, fmax=fmax, proj=False, n_fft=4*fsA, n_overlap=2*fsA)

mpsd_B=np.mean(psd_B, axis=0)
mpsd_A=np.mean(psd_A, axis=0)

plt.plot(freqs, mpsd_B, freqs, mpsd_A)
plt.legend(('before' ,'after'))
plt.xlabel('Frequency')
plt.show()

if save_txts:
    np.savetxt('psd_ceameg.txt', (mpsd_B.T, mpsd_A.T, freqs.T))
    np.savetxt('ch_psds_' + pth.basename(sys.argv[1]) + '_bef.txt',psd_B.T)
    np.savetxt('ch_psds_' + pth.basename(sys.argv[2]) + '_aft.txt',psd_A.T)
