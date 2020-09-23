# sipemont 191128

import matplotlib.pyplot as plt
from numpy.linalg import norm
import sys
import mne
import numpy as np

fname = sys.argv[1]

# read raw file:
raw = mne.io.read_raw_fif(fname, preload=True)

# Get MISC channel data:
raw_misc = raw.copy().pick_types(meg=False, misc=True)
# ACC resultant, plot:
acc = norm(raw_misc._data[0:3,:],None,0)
# Write ACC resultant to ECG010
raw.rename_channels({'MISC010':'ECG010'})
raw.drop_channels(['ECG007'])
ch_idx=mne.pick_channels(raw.info['ch_names'],['ECG010'])
raw._data[ch_idx]=acc
sti_idx=mne.pick_channels(raw.info['ch_names'],['STI001'])
sti = raw._data[sti_idx,:]

# Epoching for acceleration, the resultant ACC channel only:
events = mne.find_events(raw, stim_channel='STI101', min_duration=0.003)
acc_epochs = mne.Epochs(raw, events, event_id=1, picks=ch_idx, tmin=0.0, tmax=0.15,
            baseline=None, detrend=None)
# export acc epochs to csv:
np.savetxt('acc.csv',np.squeeze(acc_epochs.get_data()), fmt='%5.3f', delimiter=',')
plt.plot(acc_epochs.times,np.squeeze(acc_epochs.get_data()).T, linewidth=0.5)                      
plt.show(block=True)

# Calculate +-3 SD limits for ACC over trial starts within 0-150 ms:
mean_acc=[] # mean accelerations of trial starts
for epoch in acc_epochs:
	mean_acc.append(np.mean(epoch))
acc_mean=np.mean(mean_acc)
acc_std=np.std(mean_acc)
acc_low=acc_mean-3*acc_std
acc_high=acc_mean+3*acc_std
# Find epoch indices to reject based on +-3 SD ACC values:
reject_acc=np.logical_or(mean_acc<acc_low, mean_acc>acc_high)
print("ACC reject trials: " + str(1+np.where(reject_acc)[0]))

# Epoching with rejections based on MEG, EMG
reject=dict(mag=6e-12, grad=6e-10, emg=500e-6)
epochs = mne.Epochs(raw.filter(l_freq=0.5, h_freq=150), events, event_id=1, tmin=-0.2, tmax=1.0,
            baseline=(None, 0), flat=None, proj=False, decim=2,
            detrend=None, reject_by_annotation=True, reject=reject)
# CHECK THAT INDEXING STAYS CORRECT HERE!!!
epochs.drop(reject_acc, reason="ACC")

# Then what? Plot evokeds? Compute TSEs?
epochs.average().plot_joint()