import json
import time
import numpy as np
import warnings

from itertools import repeat
from multiprocessing import Pool

from sklearn import tree
from sklearn import preprocessing
from sklearn.model_selection import KFold
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score
from sklearn.metrics import recall_score
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import BaggingClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.externals import joblib
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import normalize

from scipy.spatial import distance
from scipy.ndimage.filters import gaussian_filter


FIFTEEN_MIN_IN_SEC = 15 * 60

ground_truth = []
bucket_data = []
ground_truth_dict = {}
bucket_data_dict = {}

bucket_keys = {'count', 'retweets', 'favorites', 'followers', 'verified', 'profile_picture', 'polarity', 'subjectivity'}

# returns the time associated with the stock end time, given a stock time
def get_end_stock_time(curr):
	return str(int(curr) + FIFTEEN_MIN_IN_SEC*4);

# returns the time associated with the start of the bucket, given a stock time
def get_start_tweet_time(curr):
	return str(int(curr) - FIFTEEN_MIN_IN_SEC*4);

# given a mapping of time -> price, return all the prices
def convert_bucket_to_array(bucket):
	buck_arr = []
	for key in bucket_keys:
		buck_arr.append(bucket[key])
	return buck_arr

# looks at the data for the tweets(stored in bucket_tweets.json) and stock prices(stored in json_minute_stock.json)
# creates the data structures we need with them
def load_data():
	global ground_truth
	global bucket_data

	warnings.filterwarnings("ignore")

	with open('../data/json_minute_stock.json') as input_file:
		ground_truth_dict = json.load(input_file)
		
	with open('../data/bucketed_tweets.json') as input_file:
		bucket_data_dict = json.load(input_file)

	stock_times = ground_truth_dict.keys()
	for start_stock_time in stock_times:
		tweet_bucket_time = get_start_tweet_time(start_stock_time)
		end_stock_time = get_end_stock_time(start_stock_time)
		if (tweet_bucket_time in bucket_data_dict) and (end_stock_time in stock_times):
			start_bucket_stock = ground_truth_dict[start_stock_time]
			end_bucket_stock = ground_truth_dict[end_stock_time]
			ground_truth.append(1 if (end_bucket_stock - start_bucket_stock > 0) else 0)
			bucket_data.append(convert_bucket_to_array(bucket_data_dict[tweet_bucket_time]))

	ground_truth = np.array(ground_truth, dtype=float)
	bucket_data = np.matrix(bucket_data, dtype=float)

# Returns the classifier that we chose to use
def get_classifier():
	# n_jobs = -1 allows us to use all cores of our machine
	return RandomForestClassifier(n_estimators=10)
	# return KNeighborsClassifier()
	# return MLPClassifier(activation='logistic')
	# return AdaBoostClassifier()
	# return SVC()

# Trains the model with the data that we have and puts model into a file
def train_model(output_file_name):
	# Create the classifier and fit the data to it
	my_classifier = get_classifier()
	my_classifier.fit(bucket_data, ground_truth)

	# Dump the generated classifier to an output file for later use
	joblib.dump(my_classifier, output_file_name)

# Uses K-fold cross validation to get the accuracy, precision, recall, and f1-score associated with the model we chose
def test_model(splits):
	accurs = []
	recalls = []
	f1_scores = []
	precisions = []
	for i in range(0, 4):
		kf = KFold(n_splits=splits, shuffle=True)
		for train_index, test_index in kf.split(bucket_data):
			X_train, X_test = bucket_data[train_index], bucket_data[test_index]
			y_train, y_test = ground_truth[train_index], ground_truth[test_index]

			# Create the classifier and trains it on the the training data
			my_classifier = get_classifier()
			my_classifier.fit(X_train, y_train)

			# Tests the classifier on the testing data and prints the accuracy results
			predictions = my_classifier.predict(X_test)
			recall = recall_score(y_test, predictions)
			precision = precision_score(y_test, predictions)
			f1score = f1_score(y_test, predictions)
			accuracy = accuracy_score(y_test, predictions)
			
			accurs.append(float(accuracy))
			recalls.append(float(recall))
			precisions.append(float(precision))
			f1_scores.append(float(f1score))

		print("Running cross_fold #" + str(i+1))

	print("average precision: " + str(np.mean(precisions)))
	print("average recall: " + str(np.mean(recalls)))
	print("average f1_scores: " + str(np.mean(f1_scores)))
	print("average accuracy: " + str(np.mean(accurs)))

load_data()
print("Testing on " + str(len(ground_truth)) + " buckets")
test_model(5)
