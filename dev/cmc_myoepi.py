"""
CMC
for Myoepi project
(c)sipemont
151220
"""
import mne
import numpy as np
from mne.connectivity import spectral_connectivity, seed_target_indices
from scipy.signal import coherence

trig_start = 1 # instruction to push
trig_stop = 2 # instruction to rest
start_gap = 1 # seconds to remove after instruction to push
stop_gap = 0 # seconds to remove before instruction to rest
emg_ch = "BIO010"
meg_type = "grad"
raw_file = "/projects/tmp_proj/myoepi/201105/delta_CMC_raw_sss.fif"

# load raw, filter and pick grads
raw = mne.io.read_raw_fif(raw_file, preload=True).filter(1,100)
picks = mne.pick_types(raw.info, meg=meg_type, include=[emg_ch], exclude="bads")
# find seed-EMG and target-MEG channel indices
picks_ch_names = [raw.ch_names[i] for i in picks]
seed = picks_ch_names.index(emg_ch)
targets = np.arange(len(picks))
indices = seed_target_indices(seed, targets)

# prune raw data based on instruction events ev_start and ev_stop
#events = mne.find_events(raw, stim_channel="STI101")
events1 = mne.event.make_fixed_length_events(raw, duration=3)
events2 = mne.event.make_fixed_length_events(raw, start=2, id=2,duration=3)
events=np.concatenate([events1, events2])
events[:,0] -= raw.first_samp

#epochs = mne.Epochs(Raw, events, event_id=)
start_ev = mne.pick_events(events, include=trig_start)
stop_ev = mne.pick_events(events, include=trig_stop)
if len(start_ev) != len(stop_ev):
    # equalize
    print("Different number of start and stop instructions found!")
    start_ev = start_ev[:len(stop_ev)]

# find and combine active periods from raw data
raw.pick_channels(picks_ch_names)
raws=[]
for ev in zip(start_ev,stop_ev):
    raws.append(raw.copy().crop(ev[0][0]/raw.info["sfreq"]+start_gap,ev[1][0]/raw.info["sfreq"]-stop_gap).get_data())
#raw = raws.pop(0)
#raw.append(raws)

# Define wavelet frequencies and number of cycles
cwt_freqs = np.arange(13, 30, 2)
#cwt_n_cycles = cwt_freqs / 7.
cwt_n_cycles = 5
sfreq = raw.info["sfreq"]

# compute coherence between unrectified EMG and MEG channels
con, freqs, times, _, _ = mne.connectivity.spectral_connectivity(raws,
                method='coh',
                indices=indices,
                sfreq=sfreq,
                mode='cwt_morlet', #multitaper
                #fmin=10, fmax=40, fskip=0,
                faverage=True,
                tmin=None, tmax=None,
                mt_bandwidth=None,
                mt_adaptive=False,
                mt_low_bias=True,
                cwt_freqs=cwt_freqs,
                cwt_n_cycles=cwt_n_cycles,
                block_size=1000,
                n_jobs=16,
                verbose=True)

# plot the results (should first average across freqs?)
layout = mne.channels.find_layout(raw.info, 'meg')  # use full layout
tfr = mne.time_frequency.AverageTFR(raw.info, con, times, freqs, len(raws))
tfr.plot_topo(fig_facecolor='w', font_color='k', border='k')
