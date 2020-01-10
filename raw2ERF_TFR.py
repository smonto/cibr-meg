# simple utility to plot_joint and tfr from raw

event_id=1
reject = dict(grad=4e-10, mag=4e-12, eog=150e-6)

import mne
from sys import argv
from numpy import arange

freqs = arange(4,51,2) # for TFR
raw_file=argv[1]
ch_sets=[   'Vertex',
            'Left-temporal',
            'Right-temporal',
            'Left-parietal',
            'Right-parietal',
            'Left-occipital',
            'Right-occipital',
            'Left-frontal',
            'Right-frontal']

Raw=mne.io.read_raw_fif(raw_file)
Events=mne.find_events(Raw)
# ERF
Epochs=mne.Epochs(Raw, Events, event_id=event_id, tmin=-0.1, tmax=0.5,
        baseline=(None, 0), reject=reject, proj=False)
Evoked=Epochs.average()
Evoked.plot_joint()
# TFR
Epochs=mne.Epochs(Raw, Events, event_id=event_id, tmin=-0.4, tmax=1.2,
        baseline=(None, 0), reject=reject, proj=False)
tf=mne.time_frequency.tfr_morlet(Epochs, freqs, n_cycles=freqs/2, n_jobs=8, decim=2, return_itc=False)
tf=tf.crop(tmin=-0.2, tmax=1.0)
for ch_set in ch_sets:
    ch_sel=mne.read_selection(ch_set, info=tf.info)
    picks=mne.pick_channels(tf.info['ch_names'],ch_sel)
    tf.plot(mode='zscore', picks=picks, tmin=-0.3, tmax=1.0, baseline=(None,0), combine='mean',
        title=raw_file[:-4] + ': ' + ch_set, show=True)
print("Mission completed!")
