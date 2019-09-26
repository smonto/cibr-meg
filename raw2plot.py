# raw data plot
# simple utility to plot raw file from file name

import sys
import mne

raw_file=sys.argv[1]
ch_type=sys.argv[2]

Raw=mne.io.read_raw_fif(raw_file)
Raw.pick_types(Raw.info, ch_type=True)
Raw.plot()
