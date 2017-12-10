import json
import os.path
import threading
import requests
import sys
import datetime
import tweepy
from tweepy import OAuthHandler, Stream, StreamListener
from time import sleep

# TA Keys for submission
CONSUMER_KEY="a8cP5hihOsL74p0K3yWTW1Wtn"
CONSUMER_SECRET="yhNYrOPHQ86XP0e7lG8e8kYbo8KCwSLveo6e68sIxp2GXIsx1H"
ACCESS_TOKEN="917234971072270337-BdTFplE5lPpLSpQZJm3X1sQ6yllT8CT"
ACCESS_TOKEN_SECRET="S9yQCQrs2q06gSeikhGQZEaC4lKS1Vd4K8biYhKPCvhvj"

# Stocks in the S&P 100 Index
SNP_100 = ['$AAPL','$ABBV','$ABT','$ACN','$AGN','$AIG','$ALL',
            '$AMGN','$AMZN','$AXP','$BA','$BAC','$BIIB','$BK',
            '$BLK','$BMY','$BRK.B','$C','$CAT','$CELG','$CHTR',
            '$CL','$CMCSA','$COF','$COP','$COST','$CSCO','$CVS',
            '$CVX','$DHR','$DIS','$DUK','$DWDP','$EMR','$EXC',
            '$F','$FB','$FDX','$FOX','$FOXA','$GD','$GE','$GILD',
            '$GM','$GOOG','$GOOGL','$GS','$HAL','$HD','$HON',
            '$IBM','$INTC','$JNJ','$JPM','$KHC','$KMI','$KO',
            '$LLY','$LMT','$LOW','$MA','$MCD','$MDLZ','$MDT',
            '$MET','$MMM','$MO','$MON','$MRK','$MS','$MSFT',
            '$NEE','$NKE','$ORCL','$OXY','$PCLN','$PEP','$PFE',
            '$PG','$PM','$PYPL','$QCOM','$RTN','$SBUX','$SLB',
            '$SO','$SPG','$T','$TGT','$TWX','$TXN','$UNH','$UNP',
            '$UPS','$USB','$UTX','$V','$VZ','$WBA','$WFC','$WMT','$XOM']

# checks whether or not a tweet is considered spam
# we want to filter out tweets that have more than 3 tickers or are less than 3 words in len since they don't give much info
def is_spam(tweet):
  return len(tweet['entities']['symbols']) > 3 or len(remove_non_text(tweet).split(" ")) < 3

# removes tickers from the tweet since the individual tickers aren't relevant to evaluating the s&p 100 as a while
def remove_non_text(tweet):
  fields = {'urls', 'user_mentions', 'symbols'}
  text = tweet['text']
  for field in fields:
    for symb in tweet['entities'][field]:
      left = symb['indices'][0]
      right = symb['indices'][1]
      text = text[:left] + ('$' * (right - left)) + text[right:]
  return text.replace('$','').strip()

# since the search api can only handle 500 characters at once
# split what we want to search into multiple queries
def get_query_from_stocks(stocks):
    
    # partition all the stocks to max of 17 stocks per query -- this lmits the "complexity" of the query
    partitions = []
    curStocks = []
    for stock in stocks:
        curStocks.append(stock)
        if len(curStocks) == 17:
            partitions.append(curStocks)
            curStocks = []
    if len(curStocks) > 0:
        partitions.append(curStocks)

    # make queries
    queries = []
    for partition in partitions:
        queries.append(' OR '.join(partition))
    return queries

# creates the API to search twitter data from
def load_api():
    # authenicates the user
    auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    return tweepy.API(auth, wait_on_rate_limit=True)


file_name_map = {}
# function to add a tweet to a file
def append_to_file(file_name, data):
    global file_name_map
    # Ensure that file name does not already exist,
    # If it does exist, create append a count to the file name
    if file_name in file_name_map:
        fname = file_name_map[file_name]
    else:
        i = 0
        fname = file_name + '.json'
        while os.path.isfile(fname):
            i += 1
            fname = file_name + str(i) + '.json'
        file_name_map[file_name] = fname

    # Write the object data to a file in JSON format
    with open(fname, 'a') as outfile:
        s = ''
        for json_object in data:
            s += json.dumps(json_object) + '\n'
        outfile.write(s)



tweet_hashes = set([])
user_hashes = set([])

class TweetScraper():
    def __init__(self, stocks):
        self.queries = get_query_from_stocks(stocks)
        self.api = load_api()
        self.max_id = None

    # scrapes twitter for the stock tickers passed in the constructor
    # looks only for tweets where the id is lower than self.max_id to avoid duplicates
    # returns th number of tweets found
    def scrape(self):
        total_tweets = 0
        print(len(self.queries))
        try:
            found_ids = set()
            # queries using the search api using all the queries we made
            for query in self.queries:
                new_tweets = self.api.search(query, count=100) if self.max_id is None else self.api.search(query, count=100, max_id=self.max_id, since_id=938578038392008706)
                
                if not new_tweets:
                    print('no tweets found')
                else:
                    unique_tweets = 0
                    tweets = []

                    # for every tweet, we check if we have seen it before
                    # if not, append to the file
                    for tweet in new_tweets:
                        tweet_hashes.add(tweet._json['id'])
                        user_hashes.add(tweet._json['user']['id'])
                        
                        if tweet._json['id'] not in found_ids:
                            if is_spam(tweet._json):
                                continue
                            tweet._json['text'] = remove_non_text(tweet._json)
                            tweets.append(tweet._json)
                            found_ids.add(tweet._json['id'])
                            unique_tweets += 1
                    try:
                        append_to_file('tweets', tweets)
                    except PermissionError:
                        continue
                        
                    total_tweets += unique_tweets
                    print('found ' + str(total_tweets) + ' usuable/nonspam tweets from ' + str(len(tweet_hashes)) + ' tweets from ' + str(len(user_hashes)) + ' unique users')
            
            if(found_ids):
                self.max_id = min(found_ids) - 1

        except tweepy.TweepError as e:
            print('Error ' + e + ' occured.')
            return -1
        return total_tweets

if __name__ == '__main__':

    scraper = TweetScraper(SNP_100)

    # loop to scrape twitter data
    while(True):
        print('scraping')
        rc = scraper.scrape()
        if rc == -1:
            # if we get a tweepy error, good chance its a rate limit error so we should just sleep
            sleep(60)
        elif rc == 0:
            break
