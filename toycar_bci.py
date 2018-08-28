# -*- coding: utf-8 -*-

from pylsl import resolve_stream
from pylsl import StreamInlet

from time import sleep

import sounddevice as sd

import matplotlib.pyplot as plt

import numpy as np
import mne

# we have NIC system with 500.0 Hz sampling rate
stream_name = 'NIC'
sfreq = 500.0
chan = 1 # EEG channel of choice
l_freq = 8 # lowest frequency of interest
h_freq = 12 # highest frequency of interest
# get stream
streams = resolve_stream('type', 'EEG')
inlet = [StreamInlet(stream) for stream in streams
         if stream.name() == stream_name][0]

# set up plot
plt.ion()
fig = plt.figure()
ax = fig.add_subplot(111)

# set up sound system
audio_sfreq = 22050.0 # correct? where taken from?
sinefreq = 1000 # was 440
amplitude = 0.0
current_idx = 0

def callback(output_data, length, *args):
    global current_idx
    x = np.arange(current_idx, current_idx + length)
    sinewave = np.sin(2 * np.pi * sinefreq * x / audio_sfreq)
    output_data[:] = amplitude*sinewave[:, np.newaxis]
    current_idx += length


# create info for raw array
info = mne.create_info(['EEG 00' + str(idx+1) for idx in range(8)],
                       sfreq, ch_types='eeg')

# and with sound playing start the work
with sd.OutputStream(samplerate=audio_sfreq, channels=chan, callback=callback) as os:

    while True:

        # get data from nic
        data, timestamps = inlet.pull_chunk()

        print "Number of samples: " + str(len(data))

        # if no data, wait for nic a bit
        if len(data) < 1:
            print "Empty data"
            sleep(1)
            continue

        # create mne raw object from data
        # Todo: move Raw constructor outside of loop?
        raw = mne.io.RawArray(np.array(data).T, info)

        # get spectrum with welch method
        psds, freqs = mne.time_frequency.psd_welch(raw, fmin=4, fmax=45, n_fft=256)

        # plot things
        ax.cla()
        ax.plot(freqs, psds[0])

        # and update the amplitude
        freq_idxs = np.where((freqs > l_freq) & (freqs < h_freq))[0]
        normalization = np.mean(psds[0])
        # set up a baseline without output to find normalization
        if current_idx < 5*audio_sfreq/2:
            amplitude = 0
        else:
            amplitude = 0.1*(np.mean(psds[0][freq_idxs]) / normalization)

        # have animation and sound refresh at some rate
        plt.pause(0.5)
