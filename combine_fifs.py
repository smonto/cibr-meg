# small script for combining and writing fif-files
# usage: "python combine_fifs.py <combined-filename> <original-1_filename> [<original-2_filename> ...]"
# to guarantee FIFF size < 2GB, data are simply downsampled by the number of files
import sys
import mne
from argparse import ArgumentParser
#parse file names
parser = ArgumentParser()
parser.add_argument("combined_fname",nargs=1)
parser.add_argument("orig_fnames",nargs="+")
args = parser.parse_args()
print("Combined filename: %s" % args.combined_fname[0])
print("Original filenames: %s" % args.orig_fnames)
combined_raw = list()

# check infos match (channels)
for fname in args.orig_fnames:
    raw_tmp = mne.io.read_raw_fif(fname, preload=False)
    combined_raw.append(raw_tmp)
    if not raw_tmp.info['ch_names'] == combined_raw[0].info['ch_names']:
        print('Channel names in ' + fname + ' mismatch with ' + arg.orig_fnames[0])
        return;
    if not raw_tmp.info['sfreq'] == combined_raw[0].info['sfreq']:
        print('Sampling frequency in ' + fname + ' mismatches with ' + arg.orig_fnames[0])
        return;
    print('adding ' + fname  + ' to combined raw ' combined_fname)

# find new sampling frequency
sfreq = combined_raw[0].info['sfreq'] / len(args.orig_fnames)

# load data and resample
for raw_tmp, idx in enumerate(combined_raw):
    combined_raw[idx].load_data()
    combined_raw[idx].resample(sfreq=sfreq, npad='auto', stim_picks=None, n_jobs=4)

combined_raw = mne.concatenate_raws(combined_raw, verbose=True)
#mne.Annotations.delete here? To un-skip the bad-marked file boundaries in data
combined_raw.save(args.combined_fname)
