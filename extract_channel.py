""" Usage: python extract_channel.py output_name input_name ch_name """

import mne
import sys

import numpy as np

output_name = sys.argv[1]
input_name = sys.argv[2]
ch_name = sys.argv[3]

print("Reading file " + str(input_name))

raw = mne.io.read_raw_fif(input_name, preload=True)

if not ch_name in raw.info['ch_names']:
    raise Exception('No channel with name ' + str(ch_name) + ' found on raw.')

print("Writing to file " + str(output_name))
with open(output_name, 'w') as f:
    ch_data = raw._data[raw.info['ch_names'].index(ch_name)]
    times = raw.times.astype(np.str)
    for tidx, val in enumerate(ch_data):
        f.write('{0}, {1}\n'.format(times[tidx], val))

print("Done.")
