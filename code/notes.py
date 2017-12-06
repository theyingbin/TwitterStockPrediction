just some sample code from a previous project that might be useful

def get_classifier():
	# n_jobs = -1 allows us to use all cores of our machine
	return RandomForestClassifier(n_jobs = -1)
	# return MLP()


def train_model(output_file_name):
	# Create the classifier and fit the data to it
	my_classifier = get_classifier()
	my_classifier.fit(pixel_data, pixel_result)

	# Dump the generated classifier to an output file for later use
	joblib.dump(my_classifier, output_file_name)
	

def test_model(test_size):
	# Split the data into training and testing data
	X_train, X_test, y_train, y_test = train_test_split(pixel_data, pixel_result, test_size=test_size)

	# Create the classifier and trains it on the the training data
	my_classifier = get_classifier()
	my_classifier.fit(X_train, y_train)

	# Tests the classifier on the testing data and prints the accuracy results
	predictions = my_classifier.predict(X_test)
	print(accuracy_score(y_test, predictions))