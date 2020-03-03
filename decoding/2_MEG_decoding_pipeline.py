# multi-class pipeline classification
#
# import the functions
import mne
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from mne.decoding import SlidingEstimator
from sklearn.pipeline import make_pipeline
from mne.decoding import cross_val_multiscore
from sklearn.model_selection import cross_validate
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

# Read and filter the data
raw_fname = '/projects/training/MNE/MNE-sample-data/MEG/sample/sample_audvis_raw.fif'
raw = mne.io.read_raw_fif(raw_fname, preload=True)
raw.filter(0.5, 40)
# Get events and epochs
event_id = dict(aud_l=1, aud_r=2, vis_l=3, vis_r=4)
events = mne.find_events(raw)
epochs = mne.Epochs(raw, events, event_id, -0.1, 0.4, proj=True,
                    baseline=(None, 0), preload=True, decim=4,
                    reject=dict(mag=3e-12, grad=300e-12, eog=200e-6))
epochs.pick_types(meg='grad', exclude='bads')
# Assign data and labels to X, y
X = epochs.get_data() # has time as last extra dimension
y = epochs.events[:, -1]

# combine the processing steps into a scikit-learn pipeline object:
scaler = StandardScaler() # scales the data
svc = LinearSVC()
clf = make_pipeline(scaler, svc)
# To get results over time, we need a sliding estimator, which
# will handle each time instant as a separate sample:
slide_clf = SlidingEstimator(clf, n_jobs=4, scoring='accuracy', verbose=True)

# Then, do cross-validation, fitting and scoring in one line:
scores = cross_val_multiscore(slide_clf, X, y, cv=5, n_jobs=4)
# Cross-validation returns several scores, average over those:
score = np.mean(scores, axis=0)
print('Mean performance over time: %0.1f%%' % (100 * np.mean(score),))
# plot a figure showing temporal evolution of decoding performance:
plt.plot(epochs.times, score)
plt.axhline(.25, color='k', linestyle='--', label='chance level')
plt.xlabel('Time')
plt.ylabel('Accuracy')
plt.show()
