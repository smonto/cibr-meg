# raw_to_evoked
# simple utility to plot_joint from file name
# ToDo: give file as argument

raw_file='finger_elec_gnd_1.fif'
event_id=1

import mne

Raw=mne.io.read_raw_fif(raw_file)
Events=mne.find_events(Raw)
reject = dict(grad=4e-10, mag=4e-12, eog=150e-6)
Epochs=mne.Epochs(Raw, Events, event_id=event_id, tmin=-0.1, tmax=0.4,
        baseline=(None, 0), reject=reject, proj=True)
Evoked=Epochs.average()
Evoked.plot_joint()
