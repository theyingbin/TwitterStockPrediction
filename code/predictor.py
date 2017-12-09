import json
import time

from itertools import repeat
from multiprocessing import Pool

from sklearn import tree
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib
from sklearn.neural_network import MLPClassifier

from scipy.spatial import distance
from scipy.ndimage.filters import gaussian_filter


FIFTEEN_MIN_IN_SEC = 15 * 60

ground_truth = []
bucket_data = []
ground_truth_dict = {}
bucket_data_dict = {}

bucket_keys = {'count', 'retweets', 'favorites', 'followers', 'verified', 'profile_picture', 'polarity', 'subjectivity'}

def get_next_bucket_time(curr):
	return str(int(curr) + FIFTEEN_MIN_IN_SEC);

def convert_bucket_to_array(bucket):
	buck_arr = []
	for key in bucket_keys:
		buck_arr.append(bucket[key])
	return buck_arr

def load_data():
	global ground_truth
	global bucket_data

	with open('json_minute_stock.json') as input_file:
		ground_truth_dict = json.load(input_file)
		
	with open('bucketed_tweets.json') as input_file:
		bucket_data_dict = json.load(input_file)

	stock_times = ground_truth_dict.keys()
	for stock_time in stock_times:
		end_time_str = get_next_bucket_time(stock_time)
		if (stock_time in bucket_data_dict) and (end_time_str in stock_times):
			start_bucket_stock = ground_truth_dict[stock_time]
			end_bucket_stock = ground_truth_dict[end_time_str]
			ground_truth.append(1 if (end_bucket_stock - start_bucket_stock > 0) else 0)
			bucket_data.append(convert_bucket_to_array(bucket_data_dict[stock_time]))

	ground_truth = ground_truth[1:]
	bucket_data = bucket_data[:-1]

def get_classifier(topology_structure):
	# n_jobs = -1 allows us to use all cores of our machine
	return MLPClassifier(hidden_layer_sizes=topology_structure, activation='logistic')
	# return MLP()

def train_model(output_file_name):
	# Create the classifier and fit the data to it
	my_classifier = get_classifier()
	my_classifier.fit(bucket_data, ground_truth)

	# Dump the generated classifier to an output file for later use
	joblib.dump(my_classifier, output_file_name)

def test_model(X_train, X_test, y_train, y_test, topology_structure):
	# Split the data into training and testing data

	# Create the classifier and trains it on the the training data
	my_classifier = get_classifier(topology_structure)
	my_classifier.fit(X_train, y_train)

	# Tests the classifier on the testing data and prints the accuracy results
	predictions = my_classifier.predict(X_test)
	print(classification_report(y_test, predictions))
	print(accuracy_score(y_test, predictions))


load_data()
X_train, X_test, y_train, y_test = train_test_split(bucket_data, ground_truth, test_size=0.2, random_state=0)
# train_model("model.dmp")
for i in range(1, 120):
	test_model(X_train, X_test, y_train, y_test, tuple([i]))