import json
import time
from textblob import TextBlob

FIFTEEN_MIN_IN_SEC = 15 * 60

buckets = {}

def compute_tweet_weight(tweet):
	interactors = tweet['retweet_count'] + tweet['favorite_count']
	followers = tweet['user']['followers_count']
	user_attrs = 0.1 * (1 if (tweet['user']['verified']) else 0) + 0.05 * (0 if (tweet['user']['default_profile_image']) else 1) 
	return 1 + user_attrs + (0.05 if interactors > 20 else 0)

def get_closest_bucket(tweet_time):
	epoch_time = time.mktime(time.strptime(tweet_time,"%a %b %d %H:%M:%S +0000 %Y"))
	return int(epoch_time - (epoch_time % FIFTEEN_MIN_IN_SEC))

def add_to_buckets(tweet):
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
		buckets[bucket_time]['weight'] += tweet_weight
		buckets[bucket_time]['retweets'] += tweet_weight * tweet['retweet_count']
		buckets[bucket_time]['favorites'] += tweet_weight * tweet['favorite_count']
		buckets[bucket_time]['followers'] += tweet_weight * tweet['user']['followers_count']
		buckets[bucket_time]['verified'] += tweet_weight * (1 if (tweet['user']['verified']) else 0)
		buckets[bucket_time]['profile_picture'] += tweet_weight * (0 if (tweet['user']['default_profile_image']) else 1)

		analysis = TextBlob(tweet['text'])
		buckets[bucket_time]['polarity'] += tweet_weight * analysis.sentiment.polarity
		buckets[bucket_time]['subjectivity'] += tweet_weight * analysis.sentiment.subjectivity
		# print(tweet['created_at'] + " added to " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(bucket_time)))

with open('../data/tweets3.json') as input_file:
	for i, line in enumerate(input_file):
		line = line[:-1]
		try:
			tweet = json.loads(line)
		except ValueError:
			continue
		
		add_to_buckets(tweet)
		
for key in buckets:
	weight = buckets[key]['weight']
	buckets[key]['retweets'] /= weight
	buckets[key]['favorites'] /= weight
	buckets[key]['followers'] /= weight
	buckets[key]['verified'] /= weight
	buckets[key]['profile_picture'] /= weight
	buckets[key]['polarity'] /= weight
	buckets[key]['subjectivity'] /= weight
	
with open('../data/bucketed_tweets.json', 'w') as outfile:
	json.dump(buckets, outfile)