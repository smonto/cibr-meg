# raw data plot
# simple utility to plot raw file from file name

import sys
import mne

len(sys.argv)
raw_file=sys.argv[1]
sfreq=sys.argv[2]
ch_type=sys.argv[3]
print(ch_type)
print(type(sys.argv[3]))

Raw=mne.io.read_raw_fif(raw_file, preload=True)
Raw.resample(sfreq)
Raw.pick_types(Raw.info, ch_type=True)
Raw.plot()
