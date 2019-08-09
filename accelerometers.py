# this small script shows measured accelerometer data
# and combines the x-, y- and z-directions to RMS.
# sipemont 190325

import matplotlib.pyplot as plt
from mne.io import read_raw_fif
from numpy.linalg import norm

raw = read_raw_fif('5103_mov.fif', preload=True)
raw_misc = raw.copy().pick_types(meg=False, misc=True)
acc = norm(raw_misc._data[0:3,:],None,0)
fig=plt.subplot(4,1,4)
plt.subplot(4,1,1)
plt.plot(raw_misc._data[0])
plt.subplot(4,1,2)
plt.plot(raw_misc._data[1])
plt.subplot(4,1,3)
plt.plot(raw_misc._data[2])
plt.subplot(4,1,4)
plt.plot(acc)
plt.show(block=False)
