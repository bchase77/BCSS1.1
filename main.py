#!/usr/bin/env python
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

#import pytz
#from pytz import timezone, utc

#import sys

from datetime import datetime, date, time, timedelta
from google.appengine.api import users
from google.appengine.ext import ndb
import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

# DEFAULT_GUESTBOOK_NAME = 'default_guestbook'
# DEFAULT_TICKERBOOK_NAME = 'default_tickerbook'
DEFAULT_XACTIONBOOK_NAME = 'default_xactionbook'

# log = open("mylog.txt", 'a')
# sys.stdout = log

# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent. However, the write rate should be limited to
# ~1/second.

# def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
#     """Constructs a Datastore key for a Guestbook entity.
#
#     We use guestbook_name as the key.
#     """
#     return ndb.Key('Guestbook', guestbook_name)
#
# def tickerbook_key(tickerbook_name=DEFAULT_TICKERBOOK_NAME):
#     """Constructs a Datastore key for a Guestbook entity.
#
#     We use guestbook_name as the key.
#     """
#     return ndb.Key('Tickerbook', tickerbook_name)
#
def xactionbook_key(xactionbook_name=DEFAULT_XACTIONBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity.

    We use guestbook_name as the key.
    """
    return ndb.Key('xactionbook', xactionbook_name)

# def pP(item, toPrint):
#     "pP prints text to an HTML page with no divider"
#     item.response.write(toPrint)
#     return
#
# def pL(item, toPrint):
#     "pL prints text to an HTML page, followed by a divider"
#     item.response.write(toPrint+"<div></div>")
#     return

# utcmoment_unaware = datetime.utcnow()
# utcmoment = utcmoment_unaware.replace(tzinfo=pytz.utc)
# local_tz = pytz.timezone('PST')
# localDatetime = utcmoment.astimezone(pytz.timezone('America/Los_Angeles'))

class Transaction():
    """A possible transaction that could be done."""

    def __init__(self, callOrPut, type):
        #print("__init__ Transaction")

        monthsDict = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                      'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
                      'Sep': 9, 'Oct': 10, 'Nov': 11,
                      'Dec': 12}
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

        self.Last = self.conv(callOrPutArray[4])
        self.Change = self.conv(callOrPutArray[5 + oRecordOffset/2]) # add only 1 if it's longer
        self.Vol = self.conv(callOrPutArray[9 + oRecordOffset])
        self.Bid = self.conv(callOrPutArray[6 + oRecordOffset])
        self.Ask = self.conv(callOrPutArray[7 + oRecordOffset])
        self.OpenInt = self.conv(callOrPutArray[8 + oRecordOffset])
        self.Strike = self.conv(callOrPutArray[10 + oRecordOffset])
        self.month = callOrPutArray[11 + oRecordOffset].split('"')[1][0:3]
        self.monthNum = monthsDict[self.month]
        self.year = int(callOrPutArray[12 + oRecordOffset].split('"')[0][1:5])
        self.Type = type

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

# [START greeting]
# class Author(ndb.Model):
#     """Sub model for representing an author."""
#     identity = ndb.StringProperty(indexed=False)
#     email = ndb.StringProperty(indexed=False)
#
#
# class Greeting(ndb.Model):
#     """A main model for representing an individual Guestbook entry."""
#     author = ndb.StructuredProperty(Author)
#     content = ndb.StringProperty(indexed=False)
#     date = ndb.DateTimeProperty(auto_now_add=True)
# [END greeting]

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


# class TickerNDB(ndb.Model):
#     """A main model for representing an individual stock ticker."""
#     symbol = ndb.StringProperty(indexed=False)
#     companyName = ndb.StringProperty(indexed=False)
#     lastPrice = ndb.FloatProperty(indexed=False)
#     change = ndb.FloatProperty(indexed=False)
#     volume = ndb.FloatProperty(indexed=False)
#     bid = ndb.FloatProperty(indexed=False)
#     ask = ndb.FloatProperty(indexed=False)
#     openInt = ndb.FloatProperty(indexed=False)
#     strikePrice = ndb.FloatProperty(indexed=False)
#     strikeMonth = ndb.StringProperty(indexed=False)
#     strikeMonthNum = ndb.StringProperty(indexed=False)
#     strikeYear = ndb.IntegerProperty(indexed=False)
#     optionType = ndb.StringProperty(indexed=False)
#     date = ndb.DateTimeProperty(auto_now_add=True)
    # transaction = ndb.StructuredProperty(TransactionNDB, repeated=True)


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

        logging.info("XACTIONS:")
        logging.info(xactions)

        xForDisplay = []

        logging.info(len(xactions))
        logging.info("xactions[1]:")
        logging.info(xactions[1])

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


class EnterTicker(webapp2.RequestHandler):

    # Probably don't need trL list if we can assign ticker attributes rightly
    # trL = []
    logging.info("[] EnterTicker")

    def post(self):

        # pL(self, "ShowTransactions")

        f = open("f-1.txt", 'rb')
        s = f.read()

        list1 = s

        a = 'expiry:'
        b = '},expirations'
        expiry2 = list1.split(a,1)[-1].split(b)[0]
        expiry3 = expiry2.split('},')

        # print("Expiry: ", end="")
        # pL(self, "Expiry: ")
        # for each in expiry3:
        #     print(each[1:])
        #     pL(self, each[1:])

        a = 'expirations:['
        b = '}],puts'
        expirations2 = list1.split(a,1)[-1].split(b)[0]
        expirations3 = expirations2.split('},')

        # print("")
        # print("Expirations:")
        # pL(self," ")
        # pL(self,"Expirations:")
        # for each in expirations3:
        #     print(each[1:])
        #     pL(self,each[1:])

        a = 'puts:['
        b = '}],calls'
        puts2 = list1.split(a,1)[-1].split(b)[0]
        puts3 = puts2.split('},')

        # print("")
        # print("Puts:")
        # pL(self,".")
        # pL(self,"Puts:")
        # pP(self,"len(each[1:]):")
        # pL(self,len(puts3).__str__())
        for each in puts3:
            logging.info("puts3")
            # logging.info(each[1:])
            # print(each[1:])
            # pL(self, each[1:])

            # We set the same parent key on the 'Greeting' to ensure each
            # Greeting is in the same entity group. Queries across the
            # single entity group will be consistent. However, the write
            # rate to a single entity group should be limited to
            # ~1/second.
            # tickerbook_name = self.request.get('tickerbook_name',
            #                                   DEFAULT_TICKERBOOK_NAME)
            #
            # ticker  = TickerNDB(parent=tickerbook_key(tickerbook_name))
            #
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
            time.sleep(1)
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




# [START guestbook]
# class Guestbook(webapp2.RequestHandler):
#
#     def post(self):
        # We set the same parent key on the 'Greeting' to ensure each
        # Greeting is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        # guestbook_name = self.request.get('guestbook_name',
        #                                   DEFAULT_GUESTBOOK_NAME)
        # greeting = Greeting(parent=guestbook_key(guestbook_name))

        # if users.get_current_user():
        #     greeting.author = Author(
        #             identity=users.get_current_user().user_id(),
        #             email=users.get_current_user().email())

        # greeting.content = self.request.get('content')
        # greeting.put()

        # time.sleep(2)

        # query_params = {'guestbook_name': guestbook_name}
        # self.redirect('/?' + urllib.urlencode(query_params))
# [END guestbook]


# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    # ('/sign', Guestbook),
    ('/enterTicker', EnterTicker),
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
