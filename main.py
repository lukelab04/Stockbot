# Copyright (C) 2021 Luke LaBonte
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import csv 
import requests 
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import fromstring, ElementTree
import json
import collections
import yfinance as yf
import datetime

#Just for testing purposes to see how much I could make. 
startmoney = 1000

#Also just for testing purposes. Unless you want to repeat my tests, don't change this -- it will cause the code to gather trades from more than 15 days ago.
daysback = 0
today = datetime.date.today() - datetime.timedelta(daysback)

def gethousestocks():
    try:
        #The API that this uses requires a key which is on a separate website. I am gathering those keys here to get the data.
        #Note: The 15 here means the code searches back to get 15 days of trades. However, the website I get trades from does not update every day, so it ends up going like 30 days back. That's why the dates are more than 15 days apart.
        keys = gethousekeys(15, 0)
        trades, date = gethousetrades(keys)
        averagehousetrades(trades, date)
    except Exception as e:
        #I had the URL change on me while making this project. If that happens, visit the house stock watcher website, check the API section, and put in the new URLs. 
        print("Could not get data. (It's possible that the URL has changed.)", e)


def gethousekeys(days, back = 0):
    keys = []
    try:
        url = 'https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/filemap.xml'
        houseresp1 = requests.get(url)

        tree = ElementTree(fromstring(houseresp1.content))
        root = tree.getroot()

        for i in range(days):
            keys.append(root[i+back][0].text)
        return keys
    except Exception as e:
        print("Cannot go back that many days. Max is", len(root), "days.", e)


#Gathers trades made by members of congress on the days specified. 
def gethousetrades(keys):
    trades = []
    for key in keys:
        date = getpriceatdate(key)
        url = 'https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/' + key 
        houseresp2 = requests.get(url)

        housejson = json.loads(houseresp2.content)
        for trade in housejson:
            for transaction in trade['transactions']:
                # -- represents a trade that, for whatever reason, couldn't be recorded. It is easier to leave those out.
                if '--' not in transaction['ticker'] and "50" in transaction['amount']: #In the json document, trades are given a rough monetary estimate. 50 here means that more than $50,000 was exchanged. 
                    trades.append([transaction['ticker'], transaction['transaction_type']])
    return trades, date

def averagehousetrades(trades, date):
    currentmoney = startmoney
    bought = []
    sold = []
    for trade in trades:
        if 'sale' in trade[1]:
            sold.append(trade[0])
    for trade in trades:
        if 'purchase' in trade[1]:
            bought.append(trade[0])


    #btctr represents the bought stocks over a specific time period.
    btctr = collections.Counter(bought)
    print("Stocks to buy:", btctr.most_common(3)[0][0], btctr.most_common(3)[1][0],btctr.most_common(3)[2][0])

    #Comment out this return statement to see the analysis of the stocks picked
    return

    #sldctr represents the sold stocks over a specific time period. Its not used here, but I decided to keep it just in case.
    sldctr = collections.Counter(sold)

    total = 0
    #Prices 1 and 2 are so that I can calculate the percentage gain.
    prices1 = []
    prices2 = []
    #This hold the shares bought of a specific stock. Since we are just using 3 stocks, we only need 3 values.
    shares = [0, 0, 0]

    for i in btctr.most_common(3):
        try:
            #Uses the yahoofinance library to create a ticker object with the string ticker from the btctr list
            tkr = yf.Ticker(i[0])
            #tkr.history is a history of prices from the stock
            data1 = tkr.history(start = date)
            #This filters the price history to get the price at the date 15 days ago
            print("Price for", i[0], "at", date, data1.filter(['Close']).values[0])
            prices1.append(float(data1.filter(['Close']).values[0]))

            #Same thing here as above, but it gets the price for today, not 15 days ago
            data2 = tkr.history(start = today)
            print("Price for", i[0], "today", today, data2.filter(['Close']).values[0])
            prices2.append(float(data2.filter(['Close']).values[0]))
            total += (data2.filter(['Close']).values[0] - data1.filter(['Close']).values[0])
        except:
            continue

    print("Total increase:", total)
    outofmoney = False

    #This loops through the list of stocks, trying to buy each until there is no more money left.
    while not outofmoney:
        for j in range(len(prices1)):
            if currentmoney > prices1[j]:
                currentmoney -= prices1[j]
                shares[j] += 1
            if currentmoney < prices1[0] and currentmoney < prices1[1] and currentmoney < prices1[2]:
                outofmoney = True 
                break
    
    for j in range(len(prices1)):
        currentmoney += prices2[j] * shares[j]
    
    print("Start money: ", startmoney, "End money:", currentmoney, "Percentage increase:", (currentmoney / startmoney) * 100 - 100, '%')
    


#Helper function to extract the date from the key
def getpriceatdate(key):
    temp = key[-15:-5]
    endstr = ""
    endstr += temp[-4:]
    endstr += '-'
    endstr += temp[0:2]
    endstr += '-'
    endstr += temp[3:5]
    return endstr

print("Getting data... (this may take a few seconds)")
gethousestocks()  

