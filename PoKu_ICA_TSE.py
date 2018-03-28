'''
Script for performing the beta re-bound and evoked analyses for PoKu2
leg movement experiment, training part (Walker, Piitulainen).

sipemont 180315
'''

import mne
from mne import io, time_frequency
from mne.preprocessing import ICA, create_eog_epochs, create_ecg_epochs
import numpy as np

#%% parameters
subject='AK2'
condition='bef'
hemi='oikea'
freqs=np.arange(10,40)
bl_mode='zscore' # 'zscore' or 'percent' or 'ratio'
time_win=(-0.5,1.2) # re-bound time window in seconds
reject={'mag': 6e-12, 'grad': 6e-10}

#%% set paths, read and filter data
basepath='/projects/ankle/maxfiltered/longitudinal/' + condition + '/' + subject + '/'
fname=basepath + subject + '_SR_' + hemi + '_tsss_mc.fif'
Raw=io.read_raw_fif(fname, preload=True)
Raw.filter(1, 40, fir_design='firwin')
Events=mne.find_events(Raw)
#Picks=mne.pick_channels(Raw.ch_names,include=['MEG0431','MEG0432'])

#%% run ICA for automatic ocular & cardiac rejection (plot the rejected topos)
picks_ica=mne.pick_types(Raw.info, meg=True) # , eog=True, ecg=True, #cannot have Stim=True here in ICA
ica = ICA(n_components=0.98, method='fastica')
ica.fit(Raw, picks=picks_ica, reject=reject, decim=4)
ecg_epochs = create_ecg_epochs(Raw, ch_name='MEG0141', reject=reject) # ch_name='MEG0111') # find the ECG events automagically
eog_epochs = create_eog_epochs(Raw, reject=reject) # find the EOG events automagically
ecg_epochs.average().plot_joint(times=0)
eog_epochs.average().plot_joint(times=0)
ecg_inds, ecg_scores = ica.find_bads_ecg(ecg_epochs, ch_name='MEG0141', method='ctps', threshold=0.2)
print(ecg_inds)
eog_inds, eog_scores = ica.find_bads_eog(eog_epochs)
print(eog_inds)
#ica.plot_overlay(ecg_average, exclude=ecg_inds) # does not work?
try:
    ica.plot_components(ch_type='mag', picks=ecg_inds)
except IndexError as exc:
    pass
try:
    ica.plot_components(ch_type='mag', picks=eog_inds)
except IndexError as exc:
    pass
ica.exclude.extend(eog_inds)
ica.exclude.extend(ecg_inds)
# Save changes to the data:
Raw=ica.apply(Raw)
#Raw=ica.apply(Raw,exclude=[eog_inds]) # list of the ICA components to exclude!!!

#%% write Evoked
picks_evo=mne.pick_types(Raw.info, meg=True, stim=True, eog=True)
Epochs=mne.Epochs(Raw, Events, event_id=1, tmin=-0.2, tmax=0.5, baseline=(None,0), proj=False, picks=picks_evo, reject=reject)
Evoked=Epochs.average()
fig=Evoked.plot_joint(title=subject, show=True)
mne.write_evokeds('/projects/ankle/maxfiltered/longitudinal/' + condition + '_evokeds/' + subject + '_SR_' + hemi + '_tsss_mc_ica_ave.fif', Evoked)

#%% plot TFR and select frequency band
Epochs=mne.Epochs(Raw, Events, event_id=1, tmin=time_win[0],tmax=time_win[1], baseline=(None,0), proj=False)
try:
    Epochs.load_data()
except ValueError:
    print('Problem in loading epochs!')
    Epochs=Epochs[0:-1]
    Epochs.load_data()
Subtr_epochs=Epochs.subtract_evoked()
Ind_tfr=time_frequency.tfr_morlet(Subtr_epochs, freqs=freqs, n_cycles=4, return_itc=False, zero_mean=True, average=True, verbose=None, decim=4, n_jobs=8)
#Ind_tfr.plot(picks=[0], baseline=(0., 0.1), mode='mean', vmin=vmin, vmax=vmax, axes=ax, show=False, colorbar=False)
fig=Ind_tfr.plot_topo(picks=None, baseline=(None,0), mode=bl_mode, show=True)
# ask for the frequency limits as input:
l_freq=input('lower frequency?')
h_freq=input('higher frequency?')
# filter using the obtained frequency band
Raw_tse=Raw.copy()
Raw_tse.filter(l_freq, h_freq, fir_design='firwin', n_jobs=4)
Raw_tse.apply_hilbert(picks=None, envelope=False, n_jobs=1, n_fft='auto')
# get mean TSEs
Epochs_tse=mne.Epochs(Raw_tse,Events,tmin=time_win[0],tmax=time_win[1], baseline=(None,0), proj=False)
Epochs_tse.load_data()
Epochs_tse.subtract_evoked()
# just replace the data in-place
epochs = mne.EpochsArray(data=np.abs(Epochs_tse.get_data()), info=Epochs_tse.info, tmin=Epochs_tse.tmin)
tse_evoked=epochs.average()
tse = tse_evoked.data
tse = mne.baseline.rescale(tse, epochs.times, baseline=(None, 0), mode=bl_mode, copy=False)
#TSE=epochs.average()
tse_evoked = mne.EvokedArray(tse, info=tse_evoked.info, tmin=epochs.tmin, comment='tse')
# find channel with maximum re-bound
ch_name, latency = tse_evoked.get_peak(ch_type='grad', tmin=0.5, tmax=1, mode='pos')
print('Found maximum TSE in channel %s' % ch_name)
# save TSEs as evoked file and the maximum channel as .dat :
tse_fn = '/projects/ankle/maxfiltered/longitudinal/' + condition + '_TSEs/' + subject + '_SR_' + hemi + '_tsss_mc_ica_tse_ave.fif'
mne.write_evokeds(tse_fn, tse_evoked)
P=tse_evoked.pick_channels([ch_name]).data
np.savetxt(tse_fn[0:-3] + 'dat', P, fmt='%.3e', delimiter='\t', newline='\n')
np.savetxt('timepoints', Ind_tfr.times, fmt='%.3f', delimiter='\t', newline='\n')
