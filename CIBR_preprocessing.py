"""
Author: sipemont (JYU, CIBR)
Thanks to Anna-Maria Alexandrou and Jan Kujala

Edited:
031221

To do:
- document more thoroughly what happens
- test headpos arguments
- test how automatic file combination works (*-1.fif, *-2.fif, etc)

--------------------------------------------------------------
This script is intended for MEG data pre-processing (cleaning).

It consist of the following main steps:
- oversampled temporal projection (OTP)
- Maxfilter with temporal signal subspace separation (SSS + TSSS)
- independent component analysis (ICA)
plus possible head position tasks.

Expected arguments:
1. File names to be processed (in current directory; wildcards accepted)

Optional arguments:
--bad: bad channel names, separated by space (automatic detection if not given)
--headpos: reference head position (file or coordinates or "default") or None (for no transform)
--movecomp: do movement compensation (if cHPI on)
--fullica: display full ICA analysis, without pre-selected EOG/ECG components
--no_tsss: do not perform TSSS, only basic SSS
--no_ica: do not perform any ICA
--no_otp: do not perform OTP
--synthica: use synthetic data instead of EOG and ECG channels
--lp: low-pass frequency
--hp: high-pass frequency
--fs: resampling frequency
--combine: combine input files to a single output (check the reported order!)
--debug: for testing mode

The final pre-processed data will be saved in folder preprocessed_<folder_name>.
Intermediate results will be saved under "tmp" and "ICA" folders.
It is recommended to run only for one subject at time.

Currently, output logging is not enabled -- the best way to get processing logs
is to run the command in terminal and piping the "tee" functionality, like:
python CIBR_preprocessing.py foo.fif | tee log.txt
"""

import mne
import os
from mne.preprocessing import create_ecg_epochs, create_eog_epochs, ICA
from argparse import ArgumentParser
from matplotlib.pyplot import show
from matplotlib.pyplot import ion as pyplot_ion
from copy import deepcopy
#from collections import OrderedDict
from tkinter import Tcl
import compare_raws
import sys
sys.path.append("/opt/tools/cibr-meg/")

pyplot_ion
os.nice(20)

# CIBR MEG cross-talk correction and calibration files for MaxFilter:
ctc = '/neuro/databases/ctc/ct_sparse.fif'
cal = '/neuro/databases/sss/sss_cal.dat'

# Frequencies for filtering prior to ICA:
ica_low=1
ica_high=80

# Parse command arguments:
parser = ArgumentParser()
parser.add_argument("fnames", nargs="+", help="the files to be processed")
parser.add_argument("--bad", default=[], nargs='*', dest='bad_chs', help="list of bad channels in the files")
parser.add_argument("--headpos", dest='headpos', help="reference head position file")
parser.add_argument("--movecomp", default=False, dest='movecomp', action='store_const', const=True, help="do movement compensation?")
parser.add_argument("--fullica", default=False, dest='fullica', action='store_const', const=True, help="show all ICA components")
parser.add_argument("--no_tsss", default=False, dest='no_tsss', action='store_const', const=True, help="do not perform TSSS")
parser.add_argument("--no_ica", default=False, dest='no_ica', action='store_const', const=True, help="do not perform any ICA")
parser.add_argument("--no_otp", default=False, dest='no_otp', action='store_const', const=True, help="do not perform OTP")
parser.add_argument("--synthica", default=False, dest='synthica', action='store_const', const=True, help="reconstruct EOG/EEG from MEG for ICA")
parser.add_argument("--lp", default=0, dest='high_freq', type=float, help="low-pass frequency")
parser.add_argument("--hp", default=0, dest='low_freq', type=float, help="high-pass frequency")
parser.add_argument("--fs", default=0, dest='sfreq', type=int, help="new sampling frequency")
parser.add_argument("--combine", default=False, dest='combine_files', action='store_const', const=True, help="combine all input files")
parser.add_argument("--debug", default=False, dest='debug', action='store_const', const=True)
args = parser.parse_args()

## ---------------------------------------------------------
## Find the files to be processed and build paths:
file_list = args.fnames
# Ordering the files:
file_list = tuple(Tcl().call('lsort', '-dict', file_list))
target_dir = os.path.join(os.getcwd(), 'preprocessed_' + os.getcwd().split("/")[-1] + '/')
print("Found files (in order): {}".format(file_list))
print("Results will be written in: {}".format(target_dir))
proceed = input("Press n if these are not ok, or hit enter to accept.")
if proceed=="n":
    print("Stopping...")
    sys.exit(0)
os.makedirs(target_dir, exist_ok=True)
path_to_tmp_files = os.path.join(target_dir, 'tmp/')
os.makedirs(path_to_tmp_files, exist_ok=True)
path_to_ICA = os.path.join(target_dir, 'ICA/')
os.makedirs(path_to_ICA, exist_ok=True)
result_files=list() # collects result file names

## ---------------------------------------------------------
## Start processing loop for each file
for rawfile in file_list:
    # Set up names:
    fs = os.path.split(rawfile)
    fs = fs[1].split(".")
    #raw_name = fs[0] + '.fif'
    ica_file = path_to_ICA + fs[0] + '_ICA.fif';
    tmp_file = path_to_tmp_files + '_' if args.no_otp else 'OTP_' + 'TSSS_' + fs[0] + '.fif'
    result_file = target_dir + '_' if args.no_otp else 'OTP_' + 'TSSS' + '_' if no_ica else '_ICA_' + fs[0] + '.fif'
    if args.combine_files:
        combined_filename = target_dir + '_' if args.no_otp else 'OTP_' + 'TSSS' + '_' if no_ica else '_ICA_' + 'combined' + '.fif'
    # Read from file:
    raw = mne.io.read_raw_fif(rawfile, preload=True)
    if args.debug:
        print("\nCropping data to 30 s in debug mode.\n")
        raw.crop(10,40)
    raw_orig = deepcopy(raw).load_data().apply_proj()
    # Fix MAG coil type codes to avoid warning messages:
    raw.fix_mag_coil_types()
    # Bad channels search using Maxwell filtering, recommended 40 Hz LPF:
    if args.bad_chs==[]:
        print("\nLooking for bad channels...using initial 2 mins of data\n")
        noisy_chs, flat_chs = mne.preprocessing.find_bad_channels_maxwell(
                raw.copy().crop(10,130).filter(None, 40), origin='auto', calibration=cal,
                cross_talk=ctc, skip_by_annotation=['edge', 'bad_acq_skip'])
        args.bad_chs = noisy_chs + flat_chs
    raw.info['bads'].extend(args.bad_chs)
    print("Bad channels: {}".format(raw.info["bads"]))

    ## ---------------------------------------------------------
    ## Application of OTP on raw data:
    if (not args.debug) and (not args.no_otp):
        raw = mne.preprocessing.oversampled_temporal_projection(raw, duration=10.0)

    ## ---------------------------------------------------------
    ## Prepare head position transform
    try:
        headpos_info=mne.io.read_info(args.headpos)
        destination=headpos_info['dev_head_t']['trans'][0:3,3]
    except:
        destination=args.headpos
    if destination == "default":
        destination = (0.0, 0.0, 0.04)

    ## ---------------------------------------------------------
    ## Prepare head movement compensation
    if args.movecomp==True:
        # Load cHPI and head movement (default MEGIN parameter values):
        chpi_amp = mne.chpi.compute_chpi_amplitudes(raw, t_step_min=0.01, t_window=0.2)
        chpi_locs = mne.chpi.compute_chpi_locs(raw.info, chpi_amp, t_step_max=0.5, too_close='raise', adjust_dig=True)
        head_pos = mne.chpi.compute_head_pos(raw.info, chpi_locs, dist_limit=0.005, gof_limit=0.95, adjust_dig=True)
    else:
        # just get rid of cHPI signals if any:
        try:
            raw=mne.chpi.filter_chpi(raw, include_line = (raw.info["line_freq"] is not None))
        except RuntimeError:
            print("No cHPI signals found")
        head_pos = None

    ## ---------------------------------------------------------
    ## Apply TSSS on raw data:
    if args.no_tsss:
        raw=mne.preprocessing.maxwell_filter(raw, cross_talk=ctc, calibration=cal,
            st_duration=None, coord_frame="head",
            destination=destination, head_pos=head_pos)
    else:
        raw=mne.preprocessing.maxwell_filter(raw, cross_talk=ctc, calibration=cal,
            st_duration=10, st_correlation=0.98, coord_frame="head",
            destination=destination, head_pos=head_pos)

    ## ---------------------------------------------------------
    ## Filter and resample the raw data as needed:
    # Low-pass:
    if args.high_freq==0 and args.combine_files:
        args.high_freq=raw.info['lowpass'] / len(file_list)
    if args.high_freq>0:
        raw.filter(h_freq=args.high_freq, l_freq=None)
        raw.info['lowpass']=args.high_freq
        raw_orig.filter(h_freq=args.high_freq, l_freq=None)
        raw_orig.info['lowpass']=args.high_freq
        print("\nLow-pass frequency: {} Hz\n".format(raw.info["lowpass"]))
    # High-pass:
    if args.low_freq>0:
        raw.filter(h_freq=None, l_freq=args.low_freq)
        raw.info['highpass']=args.low_freq
        raw_orig.filter(h_freq=None, l_freq=args.low_freq)
        raw_orig.info['highpass']=args.low_freq
        print("\nHigh-pass frequency: {} Hz\n".format(raw.info["highpass"]))
    # Re-sampling :
    if args.sfreq > 0:
        raw.resample(args.sfreq)
        raw_orig.resample(args.sfreq)
        raw.info["sfreq"]=args.sfreq
        raw_orig.info["sfreq"]=args.sfreq
        print("\nSampling frequency: {} Hz\n".format(raw.info["sfreq"]))
    elif args.combine_files==True:
        args.sfreq=raw.info['sfreq'] / len(file_list)
        raw.resample(args.sfreq)
        raw_orig.resample(args.sfreq)
        raw.info["sfreq"]=args.sfreq
        raw_orig.info["sfreq"]=args.sfreq
        print("\nSampling frequency: {} Hz\n".format(raw.info["sfreq"]))

    # Save intermediate results to a temporary file:
    if not args.debug:
        raw.save(tmp_file, overwrite=True)
    if args.debug:
        args.fullica=True

    ## ---------------------------------------------------------
    if args.no_ica == False:
        ## Do ICA on the preprocessed data, mainly to remove EOG and ECG artefacts
        raw.info['bads'] = []
        # Remove EOG and ECG channels if synthetic MEG signals asked for:
        ica_picks = mne.pick_types(raw.info, meg=True, eeg=False, eog=not(args.synthica),
                                    ecog=not(args.synthica), stim=False, exclude='bads')
        ica = ICA(n_components=0.98, method='fastica', verbose=True) # random_state=1, max_iter=1000
        ica_reject = dict(grad=6000e-13, mag=6e-12)
        ica.fit(raw.copy().filter(h_freq=ica_high, l_freq=ica_low), picks=ica_picks, reject=ica_reject, decim=3)
        pyplot_ion()

        # Show full ICA if requested:
        if args.fullica:
            print("\nShowing all ICA components\n")
            ica.plot_components(ch_type='mag', inst=raw, show=False)
            ica.plot_sources(raw, show=False)
            # add showing evoked time courses - but which epochs? The most common?
            show(block=True)
        else:
            # Identify ECG components:
            #n_max_ecg = 3  # use max 3 components
            ecg_epochs = create_ecg_epochs(raw, tmin=-1.5, tmax=1.5)
            ecg_epochs.apply_baseline((-0.5, -0.2))
            ecg_epochs.average().plot_joint(title="Averaged ECG epochs", picks='mag', times=0.0)
            ecg_inds, scores_ecg = ica.find_bads_ecg(ecg_epochs)
            ica.exclude += ecg_inds
            print('Found {} ECG component(s)\n'.format(len(ecg_inds)))
            print('The scores are: {}\n'.format(scores_ecg))
            print("Click on the ECG component name to turn rejection off/on,\nor topomap to show more properties.")
            try:
                ica.plot_components(ch_type='mag', picks=ecg_inds, inst=raw, title="Confirm ECG components to be removed", show=False)
            except IndexError as exc:
                raise
            except ValueError as exc:
                print("\nNo ICA components found for ECG.\n")
            show(block=True)

            # Identify EOG components:
            #n_max_eog = 3  # use max 3 components
            eog_epochs = create_eog_epochs(raw, tmin=-0.5, tmax=0.5)
            eog_epochs.apply_baseline((-0.5, -0.2))
            eog_epochs.average().plot_joint(title="Averaged EOG epochs", picks='mag', times=0.0)
            eog_inds, scores_eog = ica.find_bads_eog(eog_epochs)
            ica.exclude += eog_inds
            print('Found {} EOG component(s)\n'.format(len(eog_inds)))
            print('The scores are: {}\n'.format(scores_eog))
            print("Click on the EOG component name to turn rejection off/on,\nor topomap to show more properties.")
            try:
                ica.plot_components(ch_type='mag', picks=eog_inds, inst=raw, title="Confirm EOG components to be removed", show=False)
            except IndexError as exc:
                raise
            except ValueError as exc:
                print("\nNo ICA components found for EOG.\n")
            show(block=True)

        # Apply ICA solution to the data:
        print("\nExcluding the following ICA components: " + str(ica.exclude))
        raw = ica.apply(raw)
        # Save ICA solution:
        if not args.debug:
            ica.save(ica_file)

    # Compare changes before/after processing:
    print("\nChecking the data {}:\n".format(str(rawfile)))
    try:
        compare_raws.main([raw_orig.pick_types(meg=True), raw.copy().pick_types(meg=True)], plot_psd=False)
    except:
        print("Could not compare data.\n - Maybe compare_raws.py not found?")

    # Save the final ICA-OTP-SSS pre-processed data:
    #if not args.debug:
    raw.save(result_file, overwrite=True)
    print("\nProcessed and saved file {}\n".format(result_file))
    result_files.append(result_file)

# Combine files if asked:
if args.combine_files:
    raw = mne.io.read_raw_fif(result_files[0], preload=True)
    for result_file in result_files[1:]:
        raw.append(mne.io.read_raw_fif(result_file, preload=True))
        os.remove(result_file)
    #if not args.debug:
    raw.save(combined_filename, overwrite=True)
    del raw
    os.remove(result_files[0])
    result_files=combined_filename
print("\nProduced the following final data files:")
print(result_files)
print("\nThank you for waiting!")
