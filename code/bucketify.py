import json
import time

FIFTEEN_IN_SEC = 15 * 60

buckets = {}

def get_closest_bucket(tweet_time):
	epoch_time = time.mktime(time.strptime(tweet_time,"%a %b %d %H:%M:%S +0000 %Y"))
	return int(epoch_time - (epoch_time % FIFTEEN_IN_SEC))

def add_to_buckets(tweet):
	tweet_time = get_closest_bucket(tweet['created_at'])
	for bucket_time in range(tweet_time - FIFTEEN_IN_SEC * 3, tweet_time + FIFTEEN_IN_SEC, FIFTEEN_IN_SEC):
		if not bucket_time in buckets:
			buckets[bucket_time] = {}
			buckets[bucket_time]['count'] = 0
			buckets[bucket_time]['retweets'] = 0
			buckets[bucket_time]['favorites'] = 0
			buckets[bucket_time]['followers'] = 0
			buckets[bucket_time]['verified'] = 0
			buckets[bucket_time]['profile_picture'] = 0
		buckets[bucket_time]['count'] += 1
		buckets[bucket_time]['retweets'] += tweet['retweet_count']
		buckets[bucket_time]['favorites'] += tweet['favorite_count']
		buckets[bucket_time]['followers'] += tweet['user']['followers_count']
		buckets[bucket_time]['verified'] += 1 if (tweet['user']['verified']) else 0
		buckets[bucket_time]['profile_picture'] += 1 if (tweet['user']['profile_image_url'] != '') else 0
		# print(tweet['created_at'] + " added to " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(bucket_time)))

with open('sample_tweets.json') as input_file:
	for i, line in enumerate(input_file):
		line = line[:-1]
		try:
			tweet = json.loads(line)
		except ValueError:
			continue
		
		add_to_buckets(tweet)
		
for key in buckets:
	count = buckets[key]['count']
	buckets[key]['retweets'] /= count
	buckets[key]['favorites'] /= count
	buckets[key]['followers'] /= count
	buckets[key]['verified'] /= count
	buckets[key]['profile_picture'] /= count
	print(buckets[key])
	
with open('bucketed_tweets.json', 'w') as outfile:
	json.dump(buckets, outfile)