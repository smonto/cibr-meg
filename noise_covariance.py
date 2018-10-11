# This small script computes the noise covariance matrix from epoched data.
# If the data are not epoched, this will be done for a requested trigger.
# The mode 'auto' will be used in computations.
# The matrix is saved to the current directory.

fname='' # raw file path
trig=[] # list of trigger values for epoching

#if not==Epochs
#    trig=input("Please give trigger number")

import mne

Raw=mne.io.read_raw_fif(fname, preload=True);

reject_ncm=dict(grad=4000e-13, # T / m (gradiometers)
              mag=4e-12, # T (magnetometers)
              eeg=40e-6, # V (EEG channels)
              eog=250e-6 # V (EOG channels)
              )

Events=mne.find_events
Epochs=mne.Epochs(Raw.filter(l_freq=0.5, h_freq=None),
    Events,
    event_id=trig,
    tmin=-0.2,
    tmax=0.0,
    baseline=(None, 0),
    reject=reject_ncm,
    detrend=0
    )

cov=mne.compute_covariance(Epochs,
    tmin=None,
    tmax=None,
    method='auto',
    n_jobs=4
    )
