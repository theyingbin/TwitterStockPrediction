import json
import os.path
import threading
import requests
import datetime

            
stock_val = 0
stock_data = []
def get_past_stock_price(stock_check_stop):
    global stock_val, stock_data
    if not stock_check_stop.is_set():
        # Query google for S&P100 Index value of the past 10 days 
		# for every minute
        stockName = 'SP100'
        period = 60
        days = '10d'
        query = {'i': period, 'p' : days, 'q': stockName, 'output': 'json'}
        r = requests.get('https://finance.google.com/finance/getprices?', params=query)
		
        #This produces a list where each list item is in the format of
        #date, close, high, low, open, volume for each minute
        data = bytes.decode(r.content)
        data_split = data.split('\n')
        data_split_clean_pre = data_split[7:-1]
        data_split_clean_pre[:] = [item.split(',') for item in data_split_clean_pre]
		
		#include only the minute and closing price for each minute.
        data_split_clean = [[item[0], item[1]] for item in data_split_clean_pre]
		
		#split up data_split_clean into "x" number of lists, "x" is number of days
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
		
        #Remove first letter from the minute 0 of each days
        #resulting value should be a number that represents the POSIX time
        #for minute 0.		
        new_list_0 = [[[item[1:] if list[0] == minute and minute[0] == item else item for item in minute] for minute in list] for list in seperate_days_data]
		
        #Convert every minute in each day into its equivalent POSIX time.
        new_list = [[[str(int(item)*60 + int(list[0][0])) if list[0] != minute and minute[0] == item else item for item in minute] for minute in list] for list in new_list_0]
		
        new_dict_ = {}
		
		#For item in list, convert the relation into a dictionary
		#Each dictionary entry maps unix time to closing price for each minute
        for list in new_list:
            for item in list:
                a = int(item[0])
                new_dict_[a] = float(item[1])
		
        #write the resulting dictionary into a json file.		
        with open('../data/json_minute_stock.json', "w") as outfile:
            json.dump(new_dict_,outfile)

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