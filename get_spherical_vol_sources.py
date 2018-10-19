# coding: utf-8

# some code to help in obtaining source estimates without MRIs
# will do single-layer spherical model, so no EEG data employed

import mne
import numpy as np
from matplotlib import pyplot as plt
import fnmatch
import os
from mne.minimum_norm import make_inverse_operator, apply_inverse
from nilearn.plotting import plot_stat_map
from nilearn.image import index_img

# User supplies:
filename = '/cibr_temp/tiina/coordinaatit_muunnettu/D_raw/764_alternateR_sss.fif'
event_ids = {"left": 1, "right": 2}
tmin=-0.2, tmax=0.8

# Read the data, prepare epoching
baseline = (None, 0)
reject = dict(grad=4e-10, mag=4e-12, eog=150e-6)
raw = mne.io.read_raw_fif(filename)
events= mne.find_events(raw)
picks = mne.pick_types(raw.info, meg=True, eog=True, eeg=False, exclude='bads')

# epoching + evoked
epochs = mne.Epochs(raw, events, event_ids, tmin=tmin, tmax=tmax, proj=True, picks=picks, baseline=baseline, reject=reject)
# now all epochs averaged to a single average category
evoked = epochs.average().pick_types(meg=True)
evoked.plot()
evoked.plot_topomap(times=np.linspace(0.05, 0.4, 5), ch_type='mag')

# Calculate and plot noise covariance
noise_cov = mne.compute_covariance(epochs, tmax=0., method=['shrunk', 'empirical'])
fig_cov, fig_spectra = mne.viz.plot_cov(noise_cov, raw.info)

# check if there is any response
evoked.plot_white(noise_cov)

# create spherical forward model
sphere = mne.make_sphere_model(info=evoked.info, r0='auto', head_radius=None)
#src = mne.setup_volume_source_space(sphere=[5.9, 0.7, 50.5,88], pos=10.) ##Had to input values
src = mne.setup_volume_source_space(sphere=sphere, bem=None, surface=None, pos=8., mindist=5., exclude=30., verbose=True)
fig=mne.viz.plot_alignment(raw.info, trans='auto', bem=sphere, eeg=False, src=src, dig=True,
        surfaces=['outer_skin','inner_skull','brain'], coord_frame='head', meg='sensors', verbose=True)

# Forward and inverese solutions:
fwd =mne.make_forward_solution(evoked.info,trans=None, src=src, bem=sphere, meg=True,
        eeg=False, n_jobs=3, verbose=True)
inv = make_inverse_operator(evoked.info, fwd, noise_cov, loose=1, depth=0.8, fixed=False)

# Get volume source estimate
snr = 3.0
inv_method = 'MNE' # or jotain muuta
lambda2 = 1.0 / snr ** 2
stc = apply_inverse(evoked, inv, lambda2=lambda2, method=inv_method, pick_ori=None)
_,tp=stc.get_peak()
tp=stc.time_as_index(tp)
img=stc.as_volume(src, dest='surf', mri_resolution=False)
plot_stat_map(index_img(img, tp), threshold=0,
              title='%s (t=%.1f s.)' % ('MNE', stc.times[tp]))

plt.figure()
plt.plot(1e3 * stc.times, stc.data[::100, :].T)
plt.xlabel('time (ms)')
plt.ylabel('%s value' % inv_method)
plt.show()
