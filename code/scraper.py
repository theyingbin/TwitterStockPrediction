import json
import os.path
import threading
import requests
import sys
import datetime
import tweepy
from tweepy import OAuthHandler, Stream, StreamListener
from twitterKeys import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
from time import sleep

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

def is_spam(tweet):
  return len(tweet['entities']['symbols']) > 3 or len(remove_non_text(tweet).split(" ")) < 3

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
    
    # partition all the stocks to max of 10 stocks per query
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

def load_api():
    # authenicates the user
    auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    # load the twitter API via tweepy
    return tweepy.API(auth)
            
stock_val = 0
stock_data = []
# def get_stock_price(stock_check_stop):
#     global stock_val, stock_data
#     if not stock_check_stop.is_set():
#         # Query google for S&P100 Index value
#         stockName = 'INDEXSP:SP100'
#         query = {'q': stockName, 'output': 'json'}
#         r = requests.get('https://finance.google.com/finance', params=query)
#         json_string = bytes.decode(r.content)
#         json_string = json_string.split("[", 1)[1]
#         json_string = json_string[:-2]
#         json_stock = json.loads(json_string)
#         stock_val = json_stock['l']
        
#         # Rerun query in 15 minutes
#         threading.Timer(15*60, get_stock_price, [stock_check_stop]).start()

#         # Also dump time and stock price to a file
#         curTime = datetime.datetime.now()
#         stockInfo = {'stock_name': stockName, 'stock_price': stock_val, 'timestamp': str(curTime)}
#         stock_data.append(stockInfo)
#         write_to_file('stock_prices', stock_data)

file_name_map = {}
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


# class StreamHandler(StreamListener):
#     def __init__(self):
#         self.scraped_data = []
#         self.tweet_count = 0
#         self.filtered_data = []
#         # We will be adding more important attributes here. we should use follower count as a metric since retweets/likes not the best
#         # May want to requery for better values for these attributes in the future
#         self.importantAttrs = ['text', 'created_at', 'quote_count', 'reply_count', 'retweet_count', 'favorite_count']
#         # We might also want to incorporate user attributes in the future
#         self.importantUserAttrs = ['followers_count', 'friends_count', 'listed_count', 'verified']

#     def on_data(self, data):
#         global stock_val

#         tweet_data = json.loads(data)
#         self.scraped_data.append(tweet_data)
#         self.tweet_count += 1

#         # Filter for the important attributes of the tweet
#         filtered_tweet = {}
#         for attr in self.importantAttrs:
#             if attr in tweet_data:
#                 filtered_tweet[attr] = tweet_data[attr]
#             else:
#                 print(attr + " doesn't exist in the tweet")

#         for attr in self.importantUserAttrs:
#             user_data = tweet_data['user']
#             if attr in user_data:
#                 filtered_tweet[attr] = user_data[attr]
#             else:
#                 print(attr + " doesn't exist in the tweet")

#         self.filtered_data.append(filtered_tweet)

#         print('#############################')
#         print('Tweet: ' + tweet_data['text'])
#         print('S&P100 Val: ' + str(stock_val))

#         # Dump data to files
#         write_to_file('sample_tweets', self.scraped_data)
#         write_to_file('filtered_tweets', self.filtered_data)

#         return True

#     def on_error(self, status):
#         print(status)  

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
            for query in self.queries:
                new_tweets = self.api.search(query, count=100) if self.max_id is None else self.api.search(query, count=100, max_id=self.max_id)
                
                print('found',len(new_tweets),'tweets')
                
                if not new_tweets:
                    print('no tweets found')
                else:
                    unique_tweets = 0
                    tweets = []
                    for tweet in new_tweets:
                        if tweet._json['id'] not in found_ids:
                            if is_spam(tweet._json):
                                continue
                            tweet._json['text'] = remove_non_text(tweet._json)
                            tweets.append(tweet._json)
                            found_ids.add(tweet._json['id'])
                            unique_tweets += 1

                    append_to_file('tweets', tweets)
                    total_tweets += unique_tweets
                    print('found ' + str(unique_tweets) + ' unique tweets')
            self.max_id = min(found_ids) - 1

        except tweepy.TweepError as e:
            print('Error ' + e + ' occured.')
            return -1
        return total_tweets

if __name__ == '__main__':

    scraper = TweetScraper(SNP_100)
    while(True):
        print('scraping')
        rc = scraper.scrape()
        if rc == -1:
            sleep(60)
        elif rc == 0:
            break
    
    # print("Starting stock value logging...")
    # stock_check_stop = threading.Event()
    # get_stock_price(stock_check_stop)

    # print("Monitoring tweets...")
    # handler = StreamHandler()
    # auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    # auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    # stream = Stream(auth, handler)
    # stream.filter(track=SNP_100, async=True)
    
