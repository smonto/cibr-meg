# raw data plot
# simple utility to plot raw file from file name
import sys
import mne

raw_file=sys.argv[1]
sfreq=sys.argv[2]
ch_type=sys.argv[3]
print(ch_type)
print(type(sys.argv[3]))
print(len(sys.argv))
print(len(sys.argv[3]))

kwargs=dict()
for kw in sys.argv[3:]:
#    kwargs={sys.argv[3]:True}
    kwargs.update({kw:True})

Raw=mne.io.read_raw_fif(raw_file, preload=True)
Raw.resample(sfreq)
Raw.pick_types(Raw.info, **kwargs)
Raw.plot()
