# small script for combining and writing fif-files
# usage: "python combine_fifs.py <combined_filename>  <original-1_filename> [<original-2_filename> ...] [--fs new_sampling_freq]"
# resampling (option --fs) often needed to guarantee FIFF file size < 2GB limit
#
# simo.p.monto & erkka.heinila at jyu.fi

from sys import exit as sysexit
from mne import concatenate_raws
from mne.io import read_raw_fif
from argparse import ArgumentParser
import warnings

# parse file names
parser = ArgumentParser()
parser.add_argument("combined_fname", nargs=1, help="the result file")
parser.add_argument("orig_fname", nargs="+", help="files to be combined")
parser.add_argument("--fs", default=0, dest='sfreq', help="new sampling frequency")
args = parser.parse_args()
print("Combined filename: %s" % args.combined_fname[0])
print("Original filenames: %s" % args.orig_fname)

# check infos match (channels) and append
combined_raw = list()
for fname in args.orig_fname:
    raw_tmp = read_raw_fif(fname, preload=False, verbose=False)
    combined_raw.append(raw_tmp)
    if not raw_tmp.info['ch_names'] == combined_raw[0].info['ch_names']:
        sysexit('Channel names in ' + fname + ' mismatch with ' + arg.orig_fname[0])
    if not raw_tmp.info['sfreq'] == combined_raw[0].info['sfreq']:
        sysexit('Sampling frequency in ' + fname + ' mismatches with ' + arg.orig_fname[0])
    else:
        print('adding ' + fname  + ' to combined raw ' + args.combined_fname[0])

# load data and resample
if args.sfreq==0:
    args.sfreq=combined_raw[0].info['sfreq']
for idx, raw_tmp in enumerate(combined_raw):
    combined_raw[idx].load_data()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=FutureWarning)
        combined_raw[idx].resample(sfreq=args.sfreq, npad='auto', stim_picks=None, n_jobs=4)

combined_raw = concatenate_raws(combined_raw, verbose=True)
#mne.Annotations.delete here? To un-skip the bad-marked file boundaries in data

# write to file
try:
    combined_raw.save(args.combined_fname[0])
except IOError:
    sysexit('FIFF file write error -- check file sizes and re-sampling for < 2 GB limit, and make sure file does not exist yet.')
except:
    sysexit('Unknown error.')
print('File combination completed!')
