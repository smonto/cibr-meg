# small script for combining and writing fif-files
# usage: "python combine_fifs.py <combined-filename> <original-1_filename> <original-2_filename> ..."
# to guarantee FIFF size < 2GB, data are simply downsampled by the number of files
#
# simo monto & erkka heinilä, JYU 2018

import sys
import mne

# parse file names

combined_fname = sys.argv[1]
raw_fnames = sys.argv[2:]
downsample_f = len(raw_fnames)
combined_raw = list()

# check infos match (channels)
for fname in raw_fnames:
    raw_tmp = mne.io.read_raw_fif(fname, preload=False)
    combined_raw.append(raw_tmp)
    if not raw_tmp.info['ch_names'] == combined_raw[0].info['ch_names']:
        print('Channel names in ' fname ' mismatch with ' raw_fnames[0])
        return;
    if not raw_tmp.info['sfreq'] == combined_raw[0].info['sfreq']:
        print('Sampling frequency in ' fname ' mismatches with ' raw_fnames[0])
        return;
    print(fname ' added to combined raw ' combined_fname)

sfreq = combined_raw[0].info['sfreq'] / downsample_f

# load data and resample
for raw_tmp, idx in enumerate(combined_raw):
    combined_raw[idx].load_data()
    combined_raw[idx].resample(sfreq=sfreq, npad='auto', stim_picks=None, n_jobs=4)

combined_raw = mne.concatenate_raws(combined_raw, verbose=True)
#mne.Annotations.delete? to un-skip the file boundaries in data
combined_raw.save(combined_fname)
