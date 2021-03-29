#!/usr/bin/env python

import json
import os

import datetime

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

BITFINEX_URL = 'https://api.bitfinex.com/v1/pubticker/btcusd'


# We set a parent key on the 'Exchange' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent. However, the write rate should be limited to
# ~1/second.

class Exchange(ndb.Model):
    """A main model for representing an individual Exchange entry."""
    mid = ndb.FloatProperty()
    bid = ndb.FloatProperty()
    ask = ndb.FloatProperty()
    last_price = ndb.FloatProperty()
    high = ndb.FloatProperty()
    low = ndb.FloatProperty()
    volume = ndb.FloatProperty()
    timestamp = ndb.DateTimeProperty(auto_now_add=True)


class FetchLocalPrices(webapp2.RequestHandler):
    pass

    def get(self):
        exchange_query = Exchange.query().order(-Exchange.timestamp)
        prices = exchange_query.fetch(100)
        priceList = []
        for item in prices:
            raw_json = {
                "key": str(item.key).strip().replace("Key('Exchange', ", "").replace(")", ""),
                "mid": str(item.mid),
                "bid": str(item.bid),
                "ask": str(item.ask),
                "last_price": str(item.last_price),
                "low": str(item.low),
                "high": str(item.high),
                "volume": str(item.volume),
                "timestamp": str(item.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            }
            priceList.append(raw_json)
            print priceList

        self.response.out.write(json.dumps(priceList))


class HealthCheck(webapp2.RequestHandler):
    def get(self):
        status = {
            "runtime": "true"
        }
        self.response.out.write(json.dumps(status))


def endpoint_call():
    try:
        result = urlfetch.fetch(BITFINEX_URL,
                                payload={},
                                method=urlfetch.GET,
                                deadline=60,
                                headers={})

        if result.status_code != 200:
            return 'Unsuccessful'
        else:
            return result.content
    except urlfetch.InvalidURLError:
        return 'invalid url'


class CallExchange(webapp2.RequestHandler):

    def get(self):
        raw_data = endpoint_call()
        if raw_data != 'invalid url' or raw_data != 'invalid url':
            res = json.loads(raw_data)
            e = Exchange(mid=float(res['mid']),
                         bid=float(res['bid']),
                         ask=float(res['ask']),
                         last_price=float(res['last_price']),
                         high=float(res['high']),
                         low=float(res['low']),
                         volume=float(res['volume']))
            e.timestamp = datetime.datetime.fromtimestamp(float(res['timestamp']))
            print "Fetching Response for: {}".format(e.timestamp)

            e.put()
            status = {
                "status": "successful"
            }
            self.response.out.write(json.dumps(status))
        else:
            status = {
                "status": "failed"
            }
            self.response.out.write(json.dumps(status))


app = webapp2.WSGIApplication([
    ('/', HealthCheck),
    ('/fetch-exchange', CallExchange),
    ('/fetch-local-prices', FetchLocalPrices),
], debug=True)
