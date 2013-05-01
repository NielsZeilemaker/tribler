import numpy as np
import cPickle

from features import create_features
from parse import load_data
from Tribler.community.gossiplearningframework.youtube_classifier.dict_vectorizer import DictVectorizer

videos, users, reviews = load_data('./')
orig_X = np.array([(x['date'], x['text'], x['user']) for x in reviews])
feats = create_features(orig_X, None)
v = DictVectorizer(sparse=False)
feats = v.fit_transform(feats)

# feats is now in vectorized format
# v.transform() is the transformation that needs to be used on test data

cPickle.dump(v, open("db/dictvectorizer.pickle", "wb"))