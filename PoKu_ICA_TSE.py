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
subject='HM16'
condition='bef/'
hemi='vasen'
freqs=np.arange(15,30)
time_win=(500,1000) # re-bound time window in milliseconds
reject={'mag': 6e-12, 'grad': 6e-10}

#%% set paths, read and filter data
basepath='/projects/ankle/maxfiltered/training/' + condition + subject + '/'
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
ica.plot_components(ch_type='mag', picks=ecg_inds)
ica.plot_components(ch_type='mag', picks=eog_inds)
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
mne.write_evokeds(basepath + condition +'_evokeds/' + subject + '_SR_' + hemi + '_tsss_mc_ica_ave.fif', Evoked)

#%% plot TFR and select frequency band
Epochs=mne.Epochs(Raw,Events,tmin=-0.5,tmax=1.2, baseline=(None,0), proj=False)
#Ind_tfr=time_frequency.tfr_morlet(Subtr_epochs, freqs=freqs, n_cycles=3, return_itc=False, zero_mean=True, average=True, verbose=None, decim=4, n_jobs=8)
Subtr_epochs=Epochs.subtract_evoked(evoked=None)
Ind_tfr=time_frequency.tfr_morlet(Subtr_epochs, freqs=freqs, n_cycles=3, return_itc=False, zero_mean=True, average=True, verbose=None, decim=4, n_jobs=8)
#Ind_tfr.plot(picks=[0], baseline=(0., 0.1), mode='mean', vmin=vmin, vmax=vmax, axes=ax, show=False, colorbar=False)
fig=Ind_tfr.plot_topo(picks=None, baseline=(None,0), mode='zscore', show=True)
# ask for the frequency limits as input:
l_freq=input('lower frequency?')
h_freq=input('higher frequency?')
fig.close()
# filter using the obtained frequency band
Raw_tse=Raw.copy()
Raw_tse.filter(l_freq, h_freq, fir_design='fir_win', n_jobs=4)
Raw_tse.apply_hilbert(picks=None, envelope=True, n_jobs=4, n_fft='auto')
# get mean TSEs
Epochs_tse=mne.Epochs(Raw_tse,Events,tmin=-0.5,tmax=1.2, baseline=(None,0), proj=False)
TSE=Epochs_tse.average()
# find channel with maximum re-bound
ch_name, latency = Evoked.get_peak(ch_type=grad/mag, tmin=0.5, tmax=1, mode='pos')
print('Found maximum TSE in channel %s' % ch_name)
# save TSEs as evoked file and the maximum channel as .dat :
tse_fn = basepath + condition +'_TSE/' + subject + '_SR_' + hemi + '_tsss_mc_ica_tse_ave.fif'
mne.write_evokeds(tse_fn, TSE)
P=TSE.pick_channels([ch_name]).data
savetxt(tse_fn[0:-3] + 'dat', P, fmt='%.3e', delimiter='\t', newline='\n')
savetxt('timepoints', Ind_tfr.times, fmt='%.3f', delimiter='\t', newline='\n')
