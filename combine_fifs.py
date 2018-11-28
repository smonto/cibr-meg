# small script for combining and writing fif-files
# usage: "python combine_fifs.py new_sampling_freq <combined_filename>  <original-1_filename> [<original-2_filename> ...]"
# please resample to guarantee FIFF size < 2GB
import sys
import mne
from argparse import ArgumentParser

# parse file names
parser = ArgumentParser()
parser.add_argument("combined_fname", nargs=1)
parser.add_argument("orig_fname", nargs="+")
parser.add_argument("--fs", default=0, dest='sfreq', help="new sampling frequency")
args = parser.parse_args()
print("Combined filename: %s" % args.combined_fname[0])
#sfreq = combined_raw[0].info['sfreq'] / len(args.orig_fname)
sfreq=args.sfreq
print("Sampling frequency for new file: %s" % sfreq)
print("Original filenames: %s" % args.orig_fname)
combined_raw = list()

# check infos match (channels)
for fname in args.orig_fname:
    raw_tmp = mne.io.read_raw_fif(fname, preload=False)
    combined_raw.append(raw_tmp)
    if not raw_tmp.info['ch_names'] == combined_raw[0].info['ch_names']:
        sys.exit('Channel names in ' + fname + ' mismatch with ' + arg.orig_fname[0])
    if not raw_tmp.info['sfreq'] == combined_raw[0].info['sfreq']:
        sys.exit('Sampling frequency in ' + fname + ' mismatches with ' + arg.orig_fname[0])
    else:
        print('adding ' + fname  + ' to combined raw ' + args.combined_fname[0])

# load data and resample
if sfreq==0:
    sfreq=combined_raw[0].info['sfreq']
for idx, raw_tmp in enumerate(combined_raw):
    combined_raw[idx].load_data()
    combined_raw[idx].resample(sfreq=sfreq, npad='auto', stim_picks=None, n_jobs=4)

combined_raw = mne.concatenate_raws(combined_raw, verbose=True)
#mne.Annotations.delete here? To un-skip the bad-marked file boundaries in data
try:
    combined_raw.save(args.combined_fname[0])
except IOError:
    sys.exit('FIFF file write error -- check file sizes and re-sampling frequency to stay < 2 GB limit and make sure file does not exist.')
except:
    sys.exit('Unknown error.')
print('File combination completed!')
