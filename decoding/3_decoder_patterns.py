# multi-class pipeline classification
#
# import the functions
import mne
import numpy as np
from sklearn.linear_model import ElasticNetCV
from mne.decoding import SlidingEstimator, LinearModel, get_coef
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

# Read the data
raw_fname = '/projects/training/MNE/MNE-sample-data/MEG/sample/sample_audvis_raw.fif'
raw = mne.io.read_raw_fif(raw_fname, preload=True)
raw.filter(0.5, 40)
events = mne.find_events(raw)
event_id = dict(aud_l=1, aud_r=2)
# Do epoching::
epochs = mne.Epochs(raw, events, event_id, -0.1, 0.4, proj=True,
                    baseline=(None, 0), preload=True, decim=4,
                    reject=dict(mag=3e-12, eog=200e-6))
epochs.pick_types(meg='grad', exclude='bads')
# assign data and labels to X, y
y = epochs.events[:, -1]
X = epochs.get_data()

# Build a pipeline with the LinearModel included:
clf = make_pipeline(StandardScaler(), LinearModel(ElasticNetCV(cv=5)))
time_decod = SlidingEstimator(clf, n_jobs=4, scoring='roc_auc', verbose=False)
# Do a perfect fit:
time_decod.fit(X, y)
# Get model coefficients as field patterns with inverse transforms:
coef = get_coef(time_decod, 'patterns_', inverse_transform=True)
# Construct an Evoked and plot:
evoked = mne.EvokedArray(coef, epochs.info, tmin=epochs.times[0])
evoked.plot_topomap(times=np.arange(0.0, 0.4001, 0.1), title='field patterns')
