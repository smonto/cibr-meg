"""
@author: analexan, sipemont (JYU, CIBR)

Edited:
100820

To do:
- ICA visualization and component selection
- continuous head position
    https://mne.tools/stable/auto_tutorials/preprocessing/plot_60_maxwell_filtering_sss.html#id8
- final signal visualization for user to check
- check if chpi was on

--------------------------------------------------------------
This script is intended for MEG data pre-processing (cleaning).

It consist of the following main steps:
- oversampled temporal projection (OTP)
- temporal signal subspace separation (TSSS)
- independent component analysis (ICA)

User input:
- the files to be processed (in current directory; wildcards accepted)
- bad channel list (manual check recommended; automatic if not given)
- reference head position file for head position alignment (optional)
- low-pass and high-pass frequencies (optional, automatic)
- resampling frequency (optional, automatic)
- the need to combine files (True/False)

The final pre-processed data will be saved next to the original data in
folder "preprocessed_<folder_name>". Intermediate results will be saved under
"tmp" and "ICA" folders.
"""

#path_to_bads  = '/autocibr/cibr/projects/password/data/raw/annamaria/files/kogn/bads/'
import mne
import os
from glob import glob
from mne.preprocessing import create_ecg_epochs, create_eog_epochs, ICA
from argparse import ArgumentParser

# CIBR cross-talk correction and calibration files for MaxFilter:
ctc = '/neuro/databases/ctc/ct_sparse.fif'
cal = '/neuro/databases/sss/sss_cal.dat'

# Parse command arguments:
parser = ArgumentParser()
parser.add_argument("fnames", nargs="+", help="the files to be processed")
parser.add_argument("--headpos", default=None, dest='ref_headpos', help="reference head position file")
parser.add_argument("--bad", default=[], dest='bad_chs', help="list of bad channels in the files")
parser.add_argument("--fs", default=0, dest='sfreq', help="new sampling frequency")
parser.add_argument("--lp", default=0, dest='high_freq', help="low-pass frequency")
parser.add_argument("--hp", default=0, dest='low_freq', help="high-pass frequency")
parser.add_argument("--comb", default=False, dest='combine_files', help="combine all files or not")
args = parser.parse_args()

# Build some paths:
target_dir = os.path.join('..', 'preprocessed/')
os.makedirs(target_dir, exist_ok=True)
path_to_tmp_files = os.path.join(target_dir, 'tmp/')
os.makedirs(path_to_tmp_files, exist_ok=True)
path_to_ICA = os.path.join(target_dir, 'ICA/')
os.makedirs(path_to_ICA, exist_ok=True)
#ref_info = mne.io.read_info(ref_file)
#destination = info['dev_head_t']

# Sort out and confirm the files to be processed:
# First, go through fnames to find final files
file_list = [glob(f) for f in args.fnames]
#print("Found files: %s" % args.fnames)
#print("Found files: %s" % args.fnames[0])
print("Found files: %s" % file_list[0])

for rawfile in file_list[0]:
    fs = rawfile.split(".")
    raw_name = fs[0] + '.fif'
    ica_file = path_to_ICA + fs[0] + '_ICA.fif';
    tmp_file = path_to_tmp_files + 'OTP_TSSS_' + fs[0] + '.fif'
    result_file = target_dir + 'OTP_TSSS_ICA_' + fs[0] + '.fif'

result_files=list() # collects result file names

# Start processing loop for each file
for rawfile in file_list:
    ## Read from file:
    raw = mne.io.read_raw_fif(rawfile, preload = True)
    # Bad channels
    if args.bad_chs==[]:
        noisy_chs, flat_chs = mne.preprocessing.find_bad_channels_maxwell(
                raw.copy.filter(None, 40), origin='auto', calibration=cal,
                cross_talk=ctc, skip_by_annotation=['edge', 'bad_acq_skip'])
        args.bad_chs = noisy_chs + flat_chs
    raw.info['bads'].extend(args.bad_chs)
    print("Bad channels: {}".format(raw.info["bads"]))
    # Filter and resample the raw data as needed:
    # if chpi was on:
    raw=mne.chpi.filter_chpi(raw, include_line=True)
    if args.high_freq==0 and args.combine_files:
        args.high_freq=raw.info['h_freq'] / len(file_list)
    if args.high_freq>0:
        raw.filter(0, args.high_freq)
        raw.info['lowpass']=args.high_freq
        print("Low-pass frequency: {}".format(raw.info["lowpass"]))
    if args.low_freq>0:
        raw.filter(args.low_freq, 0)
        raw.info['highpass']=args.low_freq
        print("High-pass frequency: {}".format(raw.info["highpass"]))
    if args.sfreq > 0:
        raw.resample(args.sfreq)
        raw.info["fs"]=args.sfreq
        print("Sampling frequency: {}".format(raw.info["fs"]))
    elif args.combine_files==True:
        args.sfreq=raw.info['fs'] / len(file_list)
        raw.resample(args.sfreq)
        raw.info["fs"]=args.sfreq
        print("Sampling frequency: {}".format(raw.info["fs"]))

    ## ---------------------------------------------------------
    ## Application of OTP:
    raw = mne.preprocessing.oversampled_temporal_projection(raw, duration=10.0)
    #info = mne.io.read_info(raw_name)

    ## ---------------------------------------------------------
    ## Apply TSSS on the data:
    #origin=info['dev_head_t']['trans'][[0,1,2],3]
    raw=mne.preprocessing.maxwell_filter(raw ,cross_talk=ctc, calibration=cal,
                        st_duration=10, st_correlation =0.999,
                        destination = args.headpos, coord_frame=head)
    # Save intermediate results to a temporary file:
    raw.save(tmp_file, overwrite=True)

    ## ---------------------------------------------------------
    ## Do ICA on the preprocessed data, mainly to remove EOG and ECG
    raw.info['bads'] = []
    ica = ICA(n_components=0.95, method='fastica', random_state=1, max_iter=1000)
    picks = mne.pick_types(raw.info, meg=True, eeg=False, eog=False,
                          stim=False, exclude='bads')
    ica.fit(raw)
    # Identify ECG components:
    n_max_ecg = 3  # use max 3 components
    ecg_epochs = create_ecg_epochs(raw, tmin=-0.5, tmax=0.5)
    ecg_epochs.apply_baseline((None, None))
    ecg_inds, scores_ecg = ica.find_bads_ecg(ecg_epochs, method='ctps')
    print('Found {} ECG component(s)'.format(len(ecg_inds)))
    ## # TODO:
    # Show ECG components
    # Ask to verify ECG components
    ica.exclude += ecg_inds[:n_max_ecg]
    # Identify EOG components:
    n_max_eog = 3  # use max 3 components
    eog_epochs = create_eog_epochs(raw, tmin=-0.5, tmax=0.5)
    eog_epochs.apply_baseline((None, None))
    eog_inds, scores_eog = ica.find_bads_eog(eog_epochs)
    print('Found {} EOG component(s)'.format(len(eog_inds)))
    ## # TODO:
    # Show EOG components
    # Ask to verify EOG components
    ica.exclude += eog_inds[:n_max_eog]
    ## # TODO:
    # Show all the other components
    # Ask for other components to be rejected

    # Save ICA solution:
    ica.save(ica_file)
    # Apply ICA solution to the data:
    raw = ica.apply(raw)
    # Save the final ICA-OTP-SSS pre-processed data
    raw.save(result_file, overwrite=True)
    print("Processed and saved file {}".format(result_file))
    result_files.append(result_file)
if combine_files:
    raw = mne.io.read_raw_fif(result_files[0])
    for result_file in result_files[1:]:
        raw.append(mne.io.read_raw_fif(result_file))
        os.remove(result_file)
    raw.save(result_files[0], overwrite=True)
    result_files=result_files[0]
print("Produced the following files:")
print(result_files)
print("Thank you for waiting!")
