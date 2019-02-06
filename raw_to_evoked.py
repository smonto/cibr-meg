# raw_to_evoked

raw_file='finger_elec_gnd_1.fif'

import mne
Raw=mne.io.read_raw_fif(raw_file)
Events=mne.find_events(Raw)
Epochs=mne.Epochs(Raw, Events, event_id=1, tmin=-0.1, tmax=0.3,
        baseline=(None, 0), proj=True)
Evoked=Epochs.average()
Evoked.plot_joint()
