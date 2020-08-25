# Usage: ipython /path/to/this/compare_raws.py raw_1.fif raw_2.fif raw_3.fif ..
# edited sipemont 250820: add def main()
from copy import deepcopy

import mne
import sys

import numpy as np
import matplotlib.pyplot as plt


def prepare_raw_for_changes(raws):
    # we will create a new info object based on the first raw
    new_info = raws[0].info.copy()
    # create a new interleaved list of channel names
    ch_names = []
    for ch_name in raws[0].info['ch_names']:
        for idx in range(len(raws)):
            ch_names.append(ch_name + ' (' + str(idx) + ')')
    # place that into the new info object
    new_info['ch_names'] = ch_names
    # do similarly to channel info dictionaries
    chs = []
    for idx, ch in enumerate(raws[0].info['chs']):
        for raw_idx in range(len(raws)):
            ch_x = deepcopy(ch)
            ch_x['ch_name'] = new_info['ch_names'][idx*len(raws)+raw_idx]
            chs.append(ch_x)
    # and place into the new info object
    new_info['chs'] = chs
    # Update nchan entry to match the new number of channels
    new_info['nchan'] = len(chs)
    # Use bads-info for coloring every other trace with different color
    new_info['bads'] = [name for idx, name in enumerate(new_info['ch_names'])
                        if idx%2 == 0]
    # Create new interleaved data array based on all the raws given
    data = np.zeros((raws[0]._data.shape[0]*len(raws), raws[0]._data.shape[1]))
    for raw_idx in range(len(raws)):
        data[raw_idx::len(raws), :] = raws[raw_idx]._data
    # Finally create a new raw object with the new data and the new info.
    raw = mne.io.RawArray(data, new_info)
    return raw

def main(raws):
    # use helper function to prepare a combination raw
    # where the channels are interleaved
    combined_raw = prepare_raw_for_changes(raws)
    print("Plotting time series")
    combined_raw.plot(block=True)
    print("Plotting PSD's")
    # Also plot power spectral densities
    fig, axes = plt.subplots(len(raws), 2, sharex=True, sharey=True)
    for idx, raw in enumerate(raws):
        raw.plot_psd(fmax=raw.info['lowpass'],
                     ax=axes[idx, :], show=False)
        axes[idx, 0].set_xlabel('Magnetometer frequency')
        axes[idx, 1].set_xlabel('Gradiometer frequency')
    fig.tight_layout()
    plt.show()
    # Don't quit before plots have been drawn
    _ = input('Have a nice day.')

# execute this code only when the script is run directly from command line
if __name__ == '__main__':
    # load the raws from paths given as commandl ine arguments
    raws = [mne.io.Raw(path, preload=True) for path in sys.argv[1:]]
    print("Low-pass filtering to 100")
    # Filter to 100 as default so that it is easy to compare files that
    # have not been maxfiltered
    for raw in raws:
        try:
            raw.filter(None, 100, verbose='error')
        except:
            pass
    print("Dropping non-common channels")
    # Find common set of channels from info objects
    common_channels = np.bitwise_and.reduce(
        [set(raw.info['ch_names']) for raw in raws])
    # Drop all the others from all the raws
    for raw in raws:
        raw.drop_channels([ch_name for ch_name in raw.info['ch_names']
                           if ch_name not in common_channels])
    print("Combining")
    main(raws)
