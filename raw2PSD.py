# simple utility to PSD for channel groups from raw
import mne
import matplotlib.pyplot as plt
from sys import argv

ch_type='mag' # 'grad' or 'mag'
reject = dict(grad=4e-10, mag=4e-12, eog=150e-6)
fmin, fmax = 2, 100
n_fft = 2000

raw_file=argv[1]
ch_sets=[   'Left-temporal',
            'Right-temporal',
            'Left-parietal',
            'Right-parietal',
            'Left-occipital',
            'Right-occipital',
            'Left-frontal',
            'Right-frontal',
            'Vertex']

Raw=mne.io.read_raw_fif(raw_file, preload=True)
Raw.pick_types(meg=ch_type)
fig=plt.figure()
fig.suptitle(raw_file)
nn=0
for ch_set in ch_sets:
    ch_sel=mne.read_selection(ch_set, info=Raw.info)
    picks=mne.pick_channels(Raw.info['ch_names'],ch_sel)
    nn+=1
    ax=plt.subplot(5,2,nn)
    ax.set_title(ch_set)
    ax.set_xlim((0,100))
    Raw.plot_psd(fmin=fmin, fmax=fmax, n_fft=n_fft, ax=ax,
                 proj=False, picks=picks, area_mode='std',
                 show=False, average=True)
plt.show()
print("Mission completed!")
