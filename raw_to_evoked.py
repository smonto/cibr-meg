# raw_to_evoked

raw_file='finger_elec_gnd_1.fif'
event_id=1

import mne
Raw=mne.io.read_raw_fif(raw_file)
Events=mne.find_events(Raw)
Epochs=mne.Epochs(Raw, Events, event_id=event_id, tmin=-0.1, tmax=0.4,
        baseline=(None, 0), proj=True)
Evoked=Epochs.average()
Evoked.plot_joint()
