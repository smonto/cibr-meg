'''
Script for performing semi-automatic ICA removal of cardiac and ocular artifacts

sipemont 190610
'''

def main(fname):
	from mne import find_events, pick_types
	from sys import argv
	from mne.io import read_raw_fif
	from mne.preprocessing import ICA, create_eog_epochs, create_ecg_epochs
	import numpy as np

	#%% parameters
	#fname=argv[1]
	reject_ica={'mag': 6e-12, 'grad': 6e-10}
	#ecg_ch='MEG0141'

	#%% read and filter data
	Raw=read_raw_fif(fname, preload=True)
	Raw.filter(1, 40, fir_design='firwin')
	Events=find_events(Raw, min_duration=0.003)

	#%% run ICA for automatic ocular & cardiac rejection (plot the rejected topos)
	picks_ica=pick_types(Raw.info, meg=True)
	ica = ICA(n_components=0.98, method='fastica')
	ica.fit(Raw, picks=picks_ica, reject=reject_ica, decim=4)
	ecg_epochs = create_ecg_epochs(Raw, reject=reject_ica) # ch_name='MEG0111') # find the ECG events automagically
	eog_epochs = create_eog_epochs(Raw, reject=reject_ica) # find the EOG events automagically
	#ecg_epochs.average().plot_joint(times=0)
	#eog_epochs.average().plot_joint(times=0)
	ecg_inds, ecg_scores = ica.find_bads_ecg(ecg_epochs, method='ctps')
	print(ecg_inds)
	eog_inds, eog_scores = ica.find_bads_eog(eog_epochs)
	print(eog_inds)
	#ica.plot_overlay(ecg_average, exclude=ecg_inds) # does not work?
	try:
	    ica.plot_components(ch_type='mag', picks=ecg_inds)
	except IndexError as exc:
	    pass
	except ValueError as exc:
		pass
	try:
	    ica.plot_components(ch_type='mag', picks=eog_inds)
	except IndexError as exc:
	    pass
	except ValueError as exc:
		pass
	ica.exclude.extend(eog_inds)
	ica.exclude.extend(ecg_inds)
	# Save changes to the data:
	#Raw.copy().crop(10,20).plot()
	Raw=ica.apply(Raw)
	#Raw.copy().crop(10,20).plot()
	#Raw=ica.apply(Raw,exclude=[eog_inds]) # list of the ICA components to exclude!!!
	return Raw, ica

if __name__=="__main__":
	main()
