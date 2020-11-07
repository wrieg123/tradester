from tradester.feeds.static import FuturesTS, SymbolsTS

from multiprocessing import Manager, Process
from copy import deepcopy 
from tqdm import tqdm

import numpy as np



def ClockManager():

    """
    FeedManager is a central 'clock' to control aspects of iterating through time.

    ...
    
    Attributes
    ----------
    calendar : list
        a list of days to iterate over
    trading_calendar : list
        a list of days within the calendar that correspond to trading days
    start_date : DateTime
        starting date of self.calendar
    end_date : DateTime
        ending date of self.calendar
    previous : DateTime
        previously seen date during iteration, begins as None
    now : DateTime
        current date during iteration, begins as None
    new_day : Boolean
        if there is a date change between self.previous and self.now, only applies for  observations that
        are not daily
    mkt_open : Boolean
        is the current day in the trading calendar
    now_date : String
        self.now formatted as a String, YYYY-MM-DD
    prev_date : String
        self.previous formatted as a String, YYYY-MM-DD
    
    Methods
    -------
    set_bar(bar)
        not actually sure if I use this, but in theory it would set a self.bar attribute = input bar
    set_calendar(cal)
        sets the self.calendar attribute
    set_trading_calendar(cal):
        sets the self.trading_calendar attribute
    update()
        updates the self.now and self.previous pointers through iteration of calendar object
    """
    
    def __init__(self):
        self.calendar = None
        self.trading_calendar = None
        self.start_date = None 
        self.end_date = None
        self.previous = None
        self.now = None
        self.new_day = False
    
    @property
    def mkt_open(self):
        return self.now_date in self.trading_calendar

    @property
    def now_date(self):
        return self.now.strftime('%Y-%m-%d') 

    @property 
    def prev_date(self):    
        return self.previous.strftime('%Y-%m-%d')

    def set_bar(self,bar):
        self.bar = bar

    def set_calendar(self, cal):
        self.calendar = cal 
        self.end_date = max(cal)
        self.start_date = min(cal)
    
    def set_trading_calendar(self, cal):
        self.trading_calendar = list(set([x.strftime('%Y-%m-%d') for x in cal]))
    
    def update(self):   
        try:
            self.previous = deepcopy(self.now)
            self.now = self.calendar.pop(0)

            if not self.previous is None:
                self.new_day = self.now_date > self.prev_date
            else:
                self.new_day = True 
        except:
            self.now = 'END'

class Worker():
    """
    A Worker is the fundamental unit of an Active Feed. It provides the ultimate basis for centralized memory
    management of streams of data.

    ...

    Parameters
    ----------
    identifier : String
        identifier of the Feed
    start_date : String, optional
        a YYYY-MM-DD string representing a start date
    end_date : String, optional
        a YYYY-MM-DD string representing a end date
    feed : Dictionary (kind of a confusing name, my bad - Will), optional
        a dictionary of values where the key is DateTime object
    mananger : ClockManager(), optional **DO NOT MODIFY**
        the manager object when craeted like this means that all feeds share the same self.manager
    cache : Integer, optional
        if not None, how much data should be kept in memory

    Attributes
    ----------
    bar : Dictionary
        the representation of the current day's data
    feed_range : List
        days that are in the self.feed object (Dictionary)
    
    Methods
    -------
    set_stream(stream : tradester.feeds.active.Stream)
        sets self.stream equal to the stream variable
    check()
        if there is a stream (from set_stream(stream)) 

    """

    def __init__(self, identifier, start_date = None, end_date = None, feed = None, manager = ClockManager(), cache = None):
        self.manager = manager
        self.cache = cache
        self.identifier = identifier 
        self.start_date = start_date
        self.end_date = end_date 
        self.feed = feed 
        self.stream = None

    @property
    def bar(self):
        if self.manager.now in self.feed.keys(): 
            return self.feed[self.manager.now]
        else:
            return None

    @property
    def feed_range(self):
        return list(self.feed.keys())
    
    def set_stream(self, stream):
        self.stream = stream

    def check(self):    
        if not self.stream is None and not self.bar is None and not np.isnan(self.bar):
            self.stream.push(self.bar)


class WorkerGroup():
    """
    A WorkerGroup provides a way to group together various feeds.

    ...

    Parameters
    ----------
    identifiers : List
        a list of feed identifiers
    start_date : String, optional
        a YYYY-MM-DD string representing a start date
    end_date : String, optional
        a YYYY-MM-DD string representing a end date
    cache : Integer, optional
        if not None, how much data should be kept in memory
    
    Attributes
    ----------
    group : Dictionary
        the master group of all feeds
    active_group : Dictionary
        feeds that are considered either: 1) on the run contracts or 2) are still actively available for
        new data
    feed_range : List
        the master set of all data included through the feeds
    members: List
        identifiers of the active_group
    
    Methods
    -------
    chunk_up(l : List, n : integer)
        yields iterable of lists of length n from list l. Useful for batch loading in data from the FeedGroup
    """
    def __init__(self, identifiers, start_date = None, end_date = None, cache = None):
        self.identifiers = identifiers 
        self.cache = cache
        self.start_date = start_date
        self.end_date = end_date
        self.group = {}
        self.active = []

    @property 
    def feed_range(self):
        cal = []
        for i , f in list(self.group.items()):
           cal += f.feed_range
        cal = list(set(cal))
        cal.sort()
        return cal
    
    @property
    def members(self):
        return list(self.group.keys())

    def chunk_up(self, l, n):
        for i in range(0, len(l), n):
            yield l[i:i+n]

    def set_active(self, active):
        self.active = active

    def check_all(self):
        for i, f in self.active:
            f.check()
