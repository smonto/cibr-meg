""" Usage: python extract_annotations.py output_name input_name """

import mne
import sys

import numpy as np

output_name = sys.argv[1]
input_name = sys.argv[2]

print("Reading file " + str(input_name))

raw = mne.io.read_raw_fif(input_name, preload=True)

print(str(len(raw.annotations)) + ' annotations found.')

print("Writing to file " + str(output_name))
with open(output_name, 'w') as f:
    f.write('onset, duration, description\n')
    for annotation in raw.annotations:
        f.write(str(annotation['onset'] - raw.first_samp / raw.info['sfreq']) + ', ' + 
                str(annotation['duration']) + ', ' + str(annotation['description']) + '\n')

