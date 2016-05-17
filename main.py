#!C:\\Python27\\python

from __future__ import print_function

# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START imports]
import logging
import os
import urllib
import urllib2

from datetime import datetime, date, timedelta
import time
from time import sleep

#from google.appengine.lib.requests import requests
from google.appengine.api import users
from google.appengine.datastore.acl_pb import Entry
from google.appengine.ext import ndb
import jinja2
import webapp2
from webapp2_extras import json
import sys

logging.info(sys.version)

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

DEFAULT_XACTIONBOOK_NAME = 'default_xactionbook'
#1 DEFAULT_TICKERBOOK_NAME = 'default_tickerbook'

def xactionbook_key(xactionbook_name=DEFAULT_XACTIONBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity.
    We use guestbook_name as the key.
    """
    return ndb.Key('xactionbook', xactionbook_name)

#1 def tickerbook_key(tickerbook_name=DEFAULT_TICKERBOOK_NAME):
#1     """Constructs a Datastore key for a ticker entity.
#1     We use tickerbook_name as the key.
#1     """
#1     return ndb.Key('tickerbook', tickerbook_name)


# Mainpage:
#    Show the current list of tickers under analysis
#       Show total put maintenance required
#       Show total cash on hand (for covered puts sales)
#       Show Qty of long shares (for covered calls sales)
#       Show upcoming expirations
#    Show top put prospects
#       Show current positions and upcoming expirations
#       Show total cash on hand (for covered puts sales)
#       Show ROI in various ways
#       Show Put Maintenance required per ticker
#    Show top call prospects
#       Show current positions and upcoming expirations
#       Show Qty of long shares (for covered calls sales)
#       Show original costs and ROI if sold
#       Show cash which would come in if sold
# AddRemTicker:
#    Show current ticker list
#    Allow click button to add ticker
#    Allow click to remove ticker

class GetTicker():
    """Get ticker data and check if it's an option tradeable security. Returns 1 if found, -1 if not found"""

    def __init__(self,ticker):
        tail = '&output=json'
        urlpath1 = 'http://www.google.com/finance/option_chain?q=' + ticker + tail
        response1 = urllib2.urlopen(urlpath1)
        self.i1 = response1.read()
        self.valid = self.i1.find('expiry',0,10) # 1 = valid. -1 = options not available

class RemTicker(webapp2.RequestHandler):
    """Remove a ticker from the list"""

    def post(self):
        logging.info("|| RemTicker")

#        removeCheck = self.request.get("ViewDelete", default_value="|| No Choice")
        removeCheck = self.request.get("ViewDelete")
        logging.info("|| removeCheck")
        logging.info(removeCheck)

        if (removeCheck == "Delete"):

            # Double check they reall want to remove the symbol

            tickerToRemove = self.request.get("buttonticker", default_value="default_value")
            logging.info(tickerToRemove)
            ## Above works to here

            #TODO: Some kind of deleting worked. Clean it up! The key was to remove all the tickerbook crap
            # and then delete the old datastore keys.

    #1        allTickersQ = TickerNDB.query(ancestor=tickerbook_key(DEFAULT_TICKERBOOK_NAME))
            allTickersQ = TickerNDB.query()
            logging.info('allTickersQ')
            logging.info(allTickersQ)

            allTickers = allTickersQ.fetch()
            logging.info('allTickers')
            logging.info(allTickers)

    #1        entityQ = TickerNDB.query(TickerNDB.symbol == tickerToRemove,
    #1                                     ancestor=tickerbook_key(DEFAULT_TICKERBOOK_NAME))
            entityQ = TickerNDB.query(TickerNDB.symbol == tickerToRemove)
            logging.info('entityQ')
            logging.info(entityQ)

            entity = entityQ.get()
            logging.info('entity')
            logging.info(entity)

            entity.key.delete()
            sleep(0.2)
            self.redirect('/addRemTicker')
        else:
            tickerToView = self.request.get("buttonticker", default_value="default_value")
            logging.info(tickerToView)
            removeCheck = "View"
            self.redirect('/addRemTicker')


class AddRemTicker(webapp2.RequestHandler):
    """Add a ticker to the list"""

    def post(self):
        logging.info("|| AddRemTicker")
        # Show existing ticker list
        # Give a button and text area to add a ticker
        # Give a button to remove a ticker

#1        ticker_query = TickerNDB.query(
#1            ancestor=tickerbook_key(DEFAULT_TICKERBOOK_NAME))
        ticker_query = TickerNDB.query()
        tickers = ticker_query.fetch() # Get the whole list

        template_values = {
            'tickers': tickers,
        }

        template = JINJA_ENVIRONMENT.get_template('AddRemTicker.html')
        self.response.write(template.render(template_values))

    def get(self):
        logging.info("|| AddRemTicker")
        # Show existing ticker list
        # Give a button to add a ticker
        # Give a button to remove a ticker

#1        ticker_query = TickerNDB.query(
#1            ancestor=tickerbook_key(DEFAULT_TICKERBOOK_NAME))
        ticker_query = TickerNDB.query()
        tickers = ticker_query.fetch() # Get the whole list

        template_values = {
            'tickers': tickers,
        }

        template = JINJA_ENVIRONMENT.get_template('AddRemTicker.html')
        self.response.write(template.render(template_values))

class AddTicker(webapp2.RequestHandler):
    def post(self):
        logging.info("|| AddTicker")
        ticker = TickerNDB()
#1        ticker = TickerNDB(parent=tickerbook_key(DEFAULT_TICKERBOOK_NAME))
        ticker.symbol = self.request.get('addticker')
        logging.info(ticker.symbol)
        if ticker.symbol: # Empty strings are 'falsy'
            tkey = ticker.put()
            logging.info("tkey: " + str(tkey))
#        self.response.write(ticker.symbol + " added.")
        sleep(0.2)
        self.redirect('/addRemTicker')

class TransactionNDB(ndb.Model):
    """A main model for representing an individual stock ticker."""
    symbol = ndb.StringProperty(indexed=False)
    companyName = ndb.StringProperty(indexed=False)
    lastPrice = ndb.FloatProperty(indexed=False)
    change = ndb.FloatProperty(indexed=False)
    volume = ndb.FloatProperty(indexed=False)
    bid = ndb.FloatProperty(indexed=False)
    ask = ndb.FloatProperty(indexed=False)
    openInt = ndb.FloatProperty(indexed=False)
    strikePrice = ndb.FloatProperty(indexed=False)
    strikeMonth = ndb.StringProperty(indexed=False)
    strikeMonthNum = ndb.StringProperty(indexed=False)
    strikeYear = ndb.IntegerProperty(indexed=False)
    optionType = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

    def create(self, callOrPut, type):
        callOrPutArray = callOrPut.split(',')
        # If the length of the call or put entry is 13 then it's missing
        # the CS and CP elements. So, to index to the others, add 2.
        if (len(callOrPutArray) == 13):
            oRecordOffset = 0
        elif (len(callOrPutArray) == 15):
            oRecordOffset = 2
        else:
            oRecordOffset = 0
            print("ERROR: Option record not 13 or 15 length. Check the source file from the website.")
        # logging.info("oRecordOffset: " + oRecordOffset.__str__())
        # logging.info("Length of callOrPutArray: " + len(callOrPutArray).__str__())

        self.symbol = "WATT"
        # self.companyName = "Energous"
        self.lastPrice = self.conv(callOrPutArray[4])
        self.change = self.conv(callOrPutArray[5 + oRecordOffset/2]) # add only 1 if it's longer
        self.volume = self.conv(callOrPutArray[9 + oRecordOffset])
        self.bid = self.conv(callOrPutArray[6 + oRecordOffset])
        self.ask = self.conv(callOrPutArray[7 + oRecordOffset])
        self.openInt = self.conv(callOrPutArray[8 + oRecordOffset])
        self.strikePrice = self.conv(callOrPutArray[10 + oRecordOffset])
        self.strikeMonth = callOrPutArray[11 + oRecordOffset].split('"')[1][0:3]
        self.strikeMonthNum = callOrPutArray[11 + oRecordOffset].split('"')[1][0:3]
        self.strikeYear = int(callOrPutArray[12 + oRecordOffset].split('"')[0][1:5])
        self.optionType = type

    def conv(self, x):
        # logging.info("conv1")
        if (len(x) == 0):
            # logging.info("conv1.1")
            return 0
        else:
            # logging.info("conv1.2")
            # logging.info(x)
            # logging.info(x.split('"')[1])
            try:
                a = float(x.split('"')[1])
                return a
            except:
                if (x.split('"')[1] == '-'):
                    return 0
                else:
                    return -1

class TickerNDB(ndb.Model):
    """A main model for storing tickers we are interested in."""
    symbol = ndb.StringProperty(indexed=True)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):

        # items = []
        #
        # for i in range(1, 11):
        #     i = str(i)
        #
        #     # dict == {}
        #     # you just don't have to quote the keys
        #     an_item = dict(date="2012-02-" + i, id=i, position="here", status="waiting for the table to be displayed")
        #     items.append(an_item)

    # ... your code here ...

    #template.render(items=items)

        # guestbook_name = self.request.get('guestbook_name',
        #                                   DEFAULT_GUESTBOOK_NAME)
        # greetings_query = Greeting.query(
        #     ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        # greetings = greetings_query.fetch(3)
        #
        # tickerbook_name = self.request.get('tickerbook_name',
        #                                   DEFAULT_TICKERBOOK_NAME)
        # ticker_query = TickerNDB.query(
        #     ancestor=tickerbook_key(tickerbook_name)).order(-TickerNDB.date)
        # tickers = ticker_query.fetch(1)

        # logging.info("[] ticker length" + len(tickers).__str__())
        # logging.info(len(tickers))
        # logging.info(tickers)

        # logging.info("TICKERS:")
        # logging.info(tickers)

        xactionbook_name = self.request.get('xactionbook_name',
                                          DEFAULT_XACTIONBOOK_NAME)
        xaction_query = TransactionNDB.query(
            ancestor=xactionbook_key(xactionbook_name)).order(-TransactionNDB.date)

        xactions = xaction_query.fetch(10)

        logging.info("XACTIONS and len(xactions):")
        logging.info(xactions)

        logging.info(len(xactions))

        xForDisplay = []

        if (len(xactions)):
            logging.info("xactions[1]:")
            logging.info(xactions[1])
        else:
            logging.info("zero")

        if (len(xactions) > 0):
            for i in range(0, len(xactions)):
                # i = str(i)

                # dict == {}
                # you just don't have to quote the keys
                an_item = dict(
                    Symbol = xactions[i].symbol,
                    # companyName = xactions[i].companyName,
                    MyQty = i,
                    MyCost = i * 14,
                    MyCostPerShare = i*i,
                    Last = xactions[i].lastPrice,
                    ChgToday = xactions[i].change,
                    Contracts = 6,
                    ContractDate = xactions[i].strikeMonth,
                    Strike = xactions[i].strikePrice,
                    CostBid = xactions[i].bid,
                    CostAsk = xactions[i].ask,
                    SnapshotPrice = xactions[i].lastPrice,
                    Income = 100,
                    Profit = 101,
                    ROIForOne = 102,
                    IncPerYear = 103,
                    ROIPerYear = 104
                )
                xForDisplay.append(an_item)

        logging.info("len(xForDisplay)")
        logging.info(len(xForDisplay))

        d = datetime.now() + timedelta(hours=-4)
        # dpac = d.astimezone(-8, "Pacific",  "PST", "PDT")
        #
        localDatetime = d.strftime("%A, %d. %B %Y %I:%M%p")

        template_values = {
            # 'tickers': tickers,
            # 'tickerbook_name': urllib.quote_plus(tickerbook_name),
            # 'greetings': greetings,
            # 'guestbook_name': urllib.quote_plus(guestbook_name),
            # 'items': items,
            'localDatetime': localDatetime,
            'xactionbook_name': urllib.quote_plus(xactionbook_name),
            'transactions': xForDisplay
            # 'url': url,
            # 'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

        # user = users.get_current_user()
        # if user:
        #     url = users.create_logout_url(self.request.uri)
        #     url_linktext = 'Logout'
        # else:
        #     url = users.create_login_url(self.request.uri)
        #     url_linktext = 'Login'

        # template_values = {
        #     # 'user': user,
        #     'greetings': greetings,
        #     'guestbook_name': urllib.quote_plus(guestbook_name),
        #     # 'url': url,
        #     # 'url_linktext': url_linktext,
        # }
        #
        # template = JINJA_ENVIRONMENT.get_template('index.html')
        # self.response.write(template.render(template_values))
# [END main_page]

# Mainpage
# EnterTicker
#
# ProcessAllTickers
# Ticker
# RemoveTicker
#

class EnterTicker(webapp2.RequestHandler):

    # Probably don't need trL list if we can assign ticker attributes rightly
    # trL = []
    logging.info("[] EnterTicker")

    def post(self):

        # pL(self, "ShowTransactions")

        # ticker.symbol = self.request.get('content')

        tickerRead = self.request.get('newticker')

        logging.info(tickerRead)

        f = open("f-1.txt", 'rb')
        s = f.read()

        list1 = s

        logging.info("List1: ")
        logging.info(list1)

        a = 'puts:['
        b = '}],calls'
        puts2 = list1.split(a,1)[-1].split(b)[0]
        puts3 = puts2.split('},')

        for each in puts3:
            logging.info("puts3")

            xactionbook_name = self.request.get('xactionbook_name',
                                              DEFAULT_XACTIONBOOK_NAME)

            xaction = TransactionNDB(parent=xactionbook_key(xactionbook_name))

            # ticker.symbol = self.request.get('content')
            xaction.symbol = "Livingston"

            # tr = Transaction(each[1:], "P")  # Create a transaction for each
            # self.trL.append(tr)

            # xaction = TransactionNDB(parent=tickerbook_key(tickerbook_name))
            xaction.create(each[1:], "P")  # Create a transaction for each

            # I think I don't need this next stuff:
            # logging.info(ticker.companyName)
            # logging.info("[] ticker.lastPrice.str: " + ticker.lastPrice.__str__())
            # logging.info("[] ticker.lastPrice: " + ticker.lastPrice)
            # ticker.companyName = ticker.symbol + " Clark"
            # #ticker.symbol = ticker.symbol
            # ticker.lastPrice = tr.Last
            # ticker.change = tr.Change
            # ticker.volume = tr.Vol
            # ticker.bid = tr.Bid
            # ticker.ask = tr.Ask
            # ticker.openInt = tr.OpenInt
            # ticker.strikePrice = tr.Strike
            # # ticker.strikeMonth = tr.monthNum
            # ticker.strikeMonthNum = str(tr.monthNum)
            # ticker.strikeYear = tr.year
            # ticker.optionType = tr.Type
            #
            # ticker.put()
            # End dont' need
            sleep(1)
            xaction.put()

            # tr.pL = pL
            # tr.pL(self, each[1:])
            # pL(self, tr.Ask.__str__())
            # pL(self, tr.Bid.__str__())

            # Uncomment this to check the details of the transactions
            # for attr, value in tr.__dict__.iteritems():
            #    print(str(attr) + ": " + str(value))
            #    # print("Value: " + str(value))
            #    pL(self,str(attr) + ": " + str(value))

        # Good below start
        a = 'calls:['
        b = '}],under'
        calls2 = list1.split(a,1)[-1].split(b)[0]
        calls3 = calls2.split('},')

        # print(len(calls3))
        # print("")
        # print("Calls:")
        # pL(self,".")
        # pL(self,"Calls:")
        for each in calls3:
            # print(each[1:])
            # logging.info(each[1:])
                        # We set the same parent key on the 'Greeting' to ensure each
            # Greeting is in the same entity group. Queries across the
            # single entity group will be consistent. However, the write
            # rate to a single entity group should be limited to
            # ~1/second.
            # tickerbook_name = self.request.get('tickerbook_name',
            #                                   DEFAULT_TICKERBOOK_NAME)
            #
            # xactionbook_name = self.request.get('xactionbook_name',
            #                                   DEFAULT_XACTIONBOOK_NAME)
            #
            # ticker = TickerNDB(parent=tickerbook_key(tickerbook_name))

            xaction = TransactionNDB(parent=xactionbook_key(xactionbook_name))

            # I think I don't need this next stuff:
            # tr = Transaction(each[1:], "C")  # Create a transaction for each
            # self.trL.append(tr)

            # logging.info(ticker.optionType)
            # logging.info(ticker.ask)

            xaction.symbol = "Going thru your mind"

            xaction.create(each[1:], "C")  # Create a transaction for each

            # ticker.symbol = self.request.get('content')

            logging.info("1")
            logging.info(len(xaction.symbol))
            # logging.info(len(ticker.symbol))

            # tq = TickerNDB.query(
            #     ancestor=tickerbook_key(tickerbook_name)).order(-TickerNDB.date)
            xq = TransactionNDB.query(
                ancestor=xactionbook_key(xactionbook_name)).order(-TransactionNDB.date)

            # tqs = tq.fetch(2)
            xqs = xq.fetch(2)

            logging.info("2")
            # logging.info(len(tqs))
            logging.info(len(xqs))

            # ticker.companyName = ticker.symbol + " company"
            # ticker.lastPrice = tr.Last
            # ticker.change = tr.Change
            # ticker.volume = tr.Vol
            # ticker.bid = tr.Bid
            # ticker.ask = tr.Ask
            # ticker.openInt = tr.OpenInt
            # ticker.strikePrice = tr.Strike
            # # ticker.strikeMonth = tr.monthNum
            # ticker.strikeMonthNum = str(tr.monthNum)
            # ticker.strikeYear = tr.year
            # ticker.optionType = tr.Type
            #
            # ticker.put()
            # # End don't need
            time.sleep(1)
            xaction.put()

            # time.sleep(2)

            # tr.pL = pL
            # tr.pL(self, each[1:])

            # Uncomment this to check the details of the transactions
            # for attr, value in tr.__dict__.iteritems():
            #    print(str(attr) + ": " + str(value))
            #    # print("Value: " + str(value))
            #    pL(self,str(attr) + ": " + str(value))
        # Good above end

        query_params = {'xactionbook_name': xactionbook_name}
        self.redirect('/?' + urllib.urlencode(query_params))

    # def createTransactions(self, ticker):

# [END EnterTicker]

headers = {'to':'asc',
         'date':'asc',
         'type':'asc',}

# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/addRemTicker', AddRemTicker),
    ('/enterTicker', EnterTicker),
    ('/addTicker', AddTicker),
    ('/remTicker', RemTicker),
], debug=True)
# [END app]








# 2 of them look like this:
#
# [TransactionNDB(key=Key('xactionbook', 'default_xactionbook', 'TransactionNDB', 4766932662222848),
#                 ask=None,
#                 bid=None,
#                 change=None,
#                 companyName=None,
#                 date=datetime.datetime(2016, 5, 10, 15, 53, 9, 90000),
#                 lastPrice=None,
#                 openInt=None,
#                 optionType=None,
#                 strikeMonth=None,
#                 strikeMonthNum=None,
#                 strikePrice=None,
#                 strikeYear=None,
#                 symbol=u'Livingston',
#                 volume=None),
#  TransactionNDB(key=Key('xactionbook', 'default_xactionbook', 'TransactionNDB', 5470620103999488),
#                 ask=None,
#                 bid=None,
#                 change=None,
#                 companyName=None,
#                 date=datetime.datetime(2016, 5, 10, 15, 53, 6, 434000),
#                 lastPrice=None,
#                 openInt=None,
#                 optionType=None,
#                 strikeMonth=None,
#                 strikeMonthNum=None,
#                 strikePrice=None,
#                 strikeYear=None,
#                 symbol=u'Livingston',
#                 volume=None)]
