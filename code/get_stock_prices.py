import json
import os.path
import threading
import requests
import datetime
from tweepy import OAuthHandler, Stream, StreamListener


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

            
stock_val = 0
stock_data = []
def get_past_stock_price(stock_check_stop):
    global stock_val, stock_data
    if not stock_check_stop.is_set():
        # Query google for S&P100 Index value of the past 10 days 
		# for every minute
        stockName = 'SP100'
        period = 60
        days = '7d'
        query = {'i': period, 'p' : days, 'q': stockName, 'output': 'json'}
        r = requests.get('https://finance.google.com/finance/getprices?', params=query)
		
        #This produces a list where each list item is in the format of
        #date, close, high, low, open, volume for each minute
        data = bytes.decode(r.content)
        data_split = data.split('\n')
        data_split_clean = data_split[7:-1]
        data_split_clean[:] = [item.split(',') for item in data_split_clean]
			
        seperate_days_data = []
        count1 = 0
        count2 = 0
        for item in data_split_clean:
            if (len(item[0])>3 and count2 != 0):
                seperate_days_data.append(data_split_clean[count1:count2])
                count1 = count2
                count2+=1
            elif item == data_split_clean[-1]:
                seperate_days_data.append(data_split_clean[count1:count2+1])
            else:
                count2+=1
		
        thefile = open('minutestock.txt', 'w')
		
		#seperate_days_data is a list that contains 7 lists, one for each days
		#Inside each day-list, each item is a list representing each minute
		#during the stock market hours.
		#Each item contains parameters in the form of date, close, high, low, open, volume for each minute
        for item in seperate_days_data:
            thefile.write("%s\n" % item)

def determine_opcl_price_1hr(data):
    minute_start = 0
    bucket_interval = 60
	
file_name_map = {}
def write_to_file(file_name, data):
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
    with open(fname, 'w') as outfile:
        outfile.write('[\n')
        for dict in data:
            json.dump(dict, outfile)
            if dict != data[-1]:
                outfile.write(',\n')
        outfile.write('\n]')

if __name__ == '__main__':
    print("Starting stock value logging...")
    stock_check_stop = threading.Event()
    get_past_stock_price(stock_check_stop)