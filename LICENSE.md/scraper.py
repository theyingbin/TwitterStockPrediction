import json
import os.path
import threading
import requests
from tweepy import OAuthHandler, Stream, StreamListener

CONSUMER_KEY = 'getyoown'
CONSUMER_SECRET = 'getyoown'
ACCESS_TOKEN = 'getyoown'
ACCESS_TOKEN_SECRET = 'getyoown'

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

stock_val = 0

def get_stock_price(stock_check_stop):
    global stock_val
    if not stock_check_stop.is_set():
        query = {'q': 'INDEXSP:SP100', 'output': 'json'}
        r = requests.get('https://finance.google.com/finance', params=query)
        json_string = bytes.decode(r.content)
        json_string = json_string.split("[", 1)[1]
        json_string = json_string[:-2]
        json_stock = json.loads(json_string)
        stock_val = json_stock['l']
        threading.Timer(15*60, get_stock_price, [stock_check_stop]).start()

        # Also dump time and stock price to a file

def write_to_file(file_name, data):
    i = 0
    fname = file_name + '.json'
    while os.path.isfile(fname):
        i += 1
        fname = file_name + str(i) + '.json'

    with open(fname, 'w') as outfile:
        json.dump(data, outfile)

class StreamHandler(StreamListener):
    scraped_data = []
    tweet_count = 0

    def on_data(self, data):
        global stock_val

        tweet_data = json.loads(data)
        self.scraped_data.append(tweet_data)
        self.tweet_count += 1

        print('#############################')
        print('Tweet: ' + tweet_data['text'])
        print('S&P100 Val: ' + str(stock_val))

        if self.tweet_count > 499:
            write_to_file('sample_json', scraped_data)
            self.scraped_data = {}
            self.tweet_count = 0

        # Add code to also process the tweet data (basically only keep the relevant data),
        # add it to a different array and dump it to a different file

        return True

    def on_error(self, status):
        print(status)  

if __name__ == '__main__':
    try:
        print("Starting stock value logging...")
        stock_check_stop = threading.Event()
        get_stock_price(stock_check_stop)

        print("Monitoring tweets...")
        handler = StreamHandler()
        auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        stream = Stream(auth, handler)
        stream.filter(track=SNP_100, async=True)
    except (KeyboardInterrupt, SystemExit):
        write_to_file('sample_json', handler.scraped_data)
