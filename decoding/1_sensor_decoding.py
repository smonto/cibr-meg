# sensor-level classification with mne-python and scikit-learn

# import the functions
import mne
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Read the data
raw_fname = '/projects/training/MNE/MNE-sample-data/MEG/sample/sample_audvis_raw.fif'
raw = mne.io.read_raw_fif(raw_fname, preload=True)
raw.filter(0.5, 30)

events = mne.find_events(raw)
event_id = dict(aud_l=1, vis_l=3) # aud_r=2, vis_r=4

# Do epoching:
epochs = mne.Epochs(raw, events, event_id, -0.1, 0.2, proj=True,
                    picks='grad', baseline=None, preload=True)

# Get epoch labels (categories)
labels = epochs.events[:, -1]

# get only one sample (100 ms) per epoch now:
X = epochs.get_data()
X = X[:, :, epochs.time_as_index(0.1)].squeeze()

# scale the data, using sklearn standard transform and notation:
scaler = StandardScaler()
X = scaler.fit_transform(X)

# split to train and test sets:
train_X = X[50:,:]
train_y = labels[50:]
test_X = X[:50,:]
test_y = labels[:50]

# initialize the classifier, logistic regression from scikit-learn:
logreg = LogisticRegression()
# fit the classifier on your MEG training data and labels:
logreg.fit(train_X, train_y)

# test how it predicts the categories for the test data:
test_res = logreg.predict(test_X)
print("Do predicted categories match the correct labels?")
print(test_res == test_y)
# to get a performance estimate directly, use the correct labels:
print("Mean accuracy: %s" % logreg.score(test_X, test_y))
