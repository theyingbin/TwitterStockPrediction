import json
import time
from textblob import TextBlob

FIFTEEN_MIN_IN_SEC = 15 * 60

buckets = {}
tweet_ids = set()

# Allows us to give each tweet a weight (return 1 means weigh all tweets equally)
def compute_tweet_weight(tweet):
	interactors = tweet['retweet_count'] + tweet['favorite_count']
	followers = tweet['user']['followers_count']
	user_attrs = 0.1 * (1 if (tweet['user']['verified']) else 0) + 0.05 * (0 if (tweet['user']['default_profile_image']) else 1) 
	return 1 + user_attrs + (0.05 if interactors > 20 else 0)

# Find the closet bucket for the tweet
def get_closest_bucket(tweet_time):
	epoch_time = time.mktime(time.strptime(tweet_time,"%a %b %d %H:%M:%S +0000 %Y"))
	return int(epoch_time - (epoch_time % FIFTEEN_MIN_IN_SEC))

# Adds a tweet to all 4 (since 60min / 15min = 4) buckets it belongs to
def add_to_buckets(tweet):
	global tweet_ids
	global buckets

	if tweet['id'] in tweet_ids:
		return

	tweet_ids.add(tweet['id']);

	tweet_time = get_closest_bucket(tweet['created_at'])
	tweet_weight = compute_tweet_weight(tweet)
	for bucket_time in range(tweet_time - FIFTEEN_MIN_IN_SEC * 3, tweet_time + FIFTEEN_MIN_IN_SEC, FIFTEEN_MIN_IN_SEC):
		if not bucket_time in buckets:
			buckets[bucket_time] = {}
			buckets[bucket_time]['count'] = 0
			buckets[bucket_time]['weight'] = 0
			buckets[bucket_time]['retweets'] = 0
			buckets[bucket_time]['favorites'] = 0
			buckets[bucket_time]['followers'] = 0
			buckets[bucket_time]['verified'] = 0
			buckets[bucket_time]['profile_picture'] = 0
			buckets[bucket_time]['polarity'] = 0
			buckets[bucket_time]['subjectivity'] = 0
		buckets[bucket_time]['count'] += 1
		buckets[bucket_time]['retweets'] += tweet['retweet_count']
		buckets[bucket_time]['favorites'] += tweet['favorite_count']
		buckets[bucket_time]['followers'] += tweet['user']['followers_count']
		buckets[bucket_time]['verified'] += (1 if (tweet['user']['verified']) else 0)
		buckets[bucket_time]['profile_picture'] += (0 if (tweet['user']['default_profile_image']) else 1)

		# Run sentiment analysis on the tweet text
		tweet['text'] = tweet['text'].replace("#", "")
		analysis = TextBlob(tweet['text'])
		# Add extra weight to some tweets (if enabled)
		buckets[bucket_time]['weight'] += tweet_weight
		buckets[bucket_time]['polarity'] += tweet_weight * analysis.sentiment.polarity
		buckets[bucket_time]['subjectivity'] += tweet_weight * analysis.sentiment.subjectivity
		# print(tweet['created_at'] + " added to " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(bucket_time)))

# Open the data file for the tweets
with open('../data/tweets.json') as input_file:
	# Loop through all the tweets in the files and add them to buckets
	for i, line in enumerate(input_file):
		if (i % 50 == 0):
			print("\r" + str(len(tweet_ids)) + " tweets processed", end="")
		line = line[:-1]
		try:
			tweet = json.loads(line)
		except ValueError:
			continue
		
		add_to_buckets(tweet)
	
	print("\r" + str(len(tweet_ids)) + " tweets processed", end="")
		
# Each bucket contains the sum for parameters of the tweets in it, here we compute the average for each
for key in buckets:
	weight = buckets[key]['weight']
	count = buckets[key]['count']
	buckets[key]['retweets'] /= count
	buckets[key]['favorites'] /= count
	buckets[key]['followers'] /= count
	buckets[key]['verified'] /= count
	buckets[key]['profile_picture'] /= count
	buckets[key]['polarity'] /= weight
	buckets[key]['subjectivity'] /= weight

# Dump the bucket data into a file (used for future training)
with open('../data/bucketed_tweets.json', 'w') as outfile:
	json.dump(buckets, outfile)

print(len(tweet_ids))