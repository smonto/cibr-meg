# Computing and showing TFRs for Katse
#
# How to do ICA for Epochs data? (only done for evoked currently?)
# Compare data from *tr_eom_epo.fif vs *_eom_epo.fif
# load the raw maxfiltered data and find_events:
# No -- use ready-made bom/eom epochs instead!
eventmap = {'return': 2, 'towards': 4, 'away/left': 8, 'away/right': 16}
#Raw=mne.io.read_raw_fif('ds/010_block2d_raw_ds_f.fif',preload=True)
#Events=mne.find_events(Raw)
Reject = dict(mag=4e-12, grad=400e-12, eog=150e-6)
TFepochs=mne.Epochs(Raw, Events, tmin=-0.1, tmax=0.9, baseline=(None,0), proj=False, reject=Reject)
Ind_tfr4=mne.time_frequency.tfr_morlet(TFepochs['4'], freqs=Freqs, n_cycles=2, return_itc=False, zero_mean=True, average=True, verbose=None, decim=5, n_jobs=3)
Ind_tfr16=Ind_tfr
Ind_tfr16.plot_topo(baseline=(None,0),mode='zscore',picks=None,vmin=-2,vmax=2)
Ind_tfr4.plot_topo(baseline=(None,0),mode='zscore',picks=None,vmin=-2,vmax=2)
