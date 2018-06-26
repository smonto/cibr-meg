# Run interactive ICA for artefact rejection
# Possibly store data in ICA form for further analysis
#
# sipemont, 260618

import numpy as np
import mne
import matplotlib.pyplot as plt
from mne.preprocessing import ICA
#from mne.preprocessing import create_eog_epochs, create_ecg_epochs

# set user options:
raw_fname='/Users/simo/Documents/Data/MNE-sample-data/MEG/sample/sample_audvis_raw.fif' # raw data file name
#--------------------------------------

# set to non-interactive
plt.ioff()
# getting data
raw = mne.io.read_raw_fif(raw_fname, preload=True)
# 1Hz high pass is often helpful for fitting ICA
# use also low-pass to possibly get neater components
raw.filter(1., 60, n_jobs=4, fir_design='firwin')

picks_meg = mne.pick_types(raw.info, meg=True, eeg=False, eog=False,
                           stim=False, exclude='bads')
reject_ica={'mag': 6e-12, 'grad': 5e-10}

ica = mne.preprocessing.ICA(n_components=15, method='fastica') #, random_state=23) only for repeatability
ica.fit(raw, picks=picks_meg, decim=3, reject=reject_ica, verbose=True)

fig=ica.plot_components(picks=None, colorbar=True, image_interp='bilinear', inst=raw, show=False)
ica.plot_sources(raw, show=False, block=True)
print('Click on the Component time series plot to remove that component')
plt.show()

# Remove components, reconstruct and save the cleaned raw data
print('Excluded components = %s' %ica.exclude)
ica.apply(raw)
while ica.exclude==[]:
    ica.exclude.extend(ica.exclude)
    ica.apply(raw)
print('ICA applied (%s components removed)' %ica.exclude)
raw.save(raw_fname + '_ICA.fif', overwrite=True)

#ica.plot_overlay(raw)
