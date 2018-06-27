# Run interactive ICA for artefact rejection.
# User gives the raw data file name as argument.
# Hint: click on the topomap to reveal further properties
# The cleaned file is save to same place, adding _ICA.fif to name
#
# Todo: store data in ICA channels form for further analysis.
#
# sipemont, 270618

# User parameters:
n_ica_comp=30 # can be relative (float) or absolute (int)
#-------------------

import mne
import sys
from os import path
import matplotlib.pyplot as plt
from mne.preprocessing import ICA
#from mne.preprocessing import create_eog_epochs, create_ecg_epochs

# raw data file name
raw_fname=sys.argv[1]

# set to non-interactive
plt.ion()
# getting data
raw = mne.io.read_raw_fif(raw_fname, preload=True)
# 1Hz high pass is often helpful for fitting ICA
# use also low-pass to possibly get neater components
raw.filter(1., 60, n_jobs=4, fir_design='firwin')

picks_meg = mne.pick_types(raw.info, meg=True, eeg=False, eog=False,
                           stim=False, exclude='bads')
reject_ica={'mag': 6e-12, 'grad': 5e-10}

ica = ICA(n_components=n_ica_comp, method='fastica')
ica.fit(raw, picks=picks_meg, decim=3, reject=reject_ica, verbose=True)

fig=ica.plot_components(picks=None, colorbar=True, image_interp='bilinear', inst=raw, show=False)
ica.plot_sources(raw, show=False)
print('Click on the Component time series plot to remove that component')
plt.show(block=True)

# Remove components, reconstruct and save the cleaned raw data
print('Excluded components = %s' %ica.exclude)
#ica.apply(raw)
#while ica.exclude==[]:
#ica.exclude.extend(ica.exclude)
ica.apply(raw)
print('ICA applied (%s components removed)' %ica.exclude)

pth,_=path.splitext(raw_fname)
raw.save(pth + '_ICA.fif', overwrite=True)

#ica.plot_overlay(raw)
