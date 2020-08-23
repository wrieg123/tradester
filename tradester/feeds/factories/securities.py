from tradester.feeds.static import SecuritiesTS
from .feed import Feed, FeedGroup

class SecuritiesFeed(Feed):
    """
    A SecuritiesFeed is a child of parent, Feed, which is build specifically to handle futures contracts.
    
    Parameters
    ----------
    contract : string
        contract identifier of the future
    start_date : String, optional
        a YYYY-MM-DD string representing a start date
    end_date : String, optional
        a YYYY-MM-DD string representing a end date
    bar : String, optional (default: 'daily')
        type of bar data the feed will produce (daily, minute, hourly: OHLCVOI, tick: NBBO, BA, BB, BV, AV)
    feed : Dictionary (kind of a confusing name, my bad - Will), optional
        a dictionary of values where the key is DateTime object
    cache : Integer, optional
        if not None, how much data should be kept in memory

    Attributes
    ----------
    bar_type : String
        type of bar data the feed will produce (daily, minute, hourly: OHLCVOI, tick: NBBO, BA, BB, BV, AV)
    
    Methods
    -------
    __check_feed()
        checks to see if a data feed was set upon class initialization. If not, access a static FuturesTS
        feed and sets self.feed. Currently, only supports daily bar types.

    See Also
    --------
    etl.feeds.active.Feed
    etl.feeds.static.FuturesTS
    """
    
    def __init__(self, ticker, start_date = None, end_date = None, bar = 'daily', feed = None, cache = None):
        super().__init__(ticker, start_date = start_date, end_date = end_date, feed = feed, cache= cache)
        self.bar_type = bar
        self.__check_feed()
    
    def __repr__(self):
        return f'<SecuritiesFeed {self.identifier} ({self.start_date.strftime("%Y-%m-%d")} -> {self.end_date.strftime("%Y-%m-%d")})>'

    def __check_feed(self):
        if self.feed is None:
            self.feed = SecuritiesTS(self.identifier, fields = 'open, high, low, close, volume', start_date = self.start_date, end_date = self.end_date, bar = self.bar_type).data.to_dict(orient= 'index')

        if self.start_date is None:
            self.start_date = min(self.feed.keys())
        if self.end_date is None:
            self.end_date = max(self.feed.keys())


class SecuritiesFactory(FeedGroup):
    """
    A SecuritiesFactory is a FeedGroup built to handle futures contracts.
    
    Parameters
    ----------
    identifiers : List, optional
        a list of futures contract identifiers
    start_date : String, optional
        a YYYY-MM-DD string representing a start date
    end_date : String, optional
        a YYYY-MM-DD string representing a end date
    bar : String, optional (default: 'daily')
        type of bar data the feed will produce (daily, minute, hourly: OHLCVOI, tick: BA, BB, BV, AV)
    cache : Integer, optional
        if not None, how much data should be kept in memory
    
    Attributes
    ----------
    bar_type : String
        type of bar data the feed will produce (daily, minute, hourly: OHLCVOI, tick: NBBO, BA, BB, BV, AV)
    not_tradeable : List
        list of contracts that do not have data
    
    Methods
    -------
    __update_group()
        upon class initialization, add in the identifier FuturesFeed objects
    _get_feed(contract : String, temp, optional : dictionary):
        returns Feed object within self.group at contract, if temp is passed in; handles support for pooling
        of multiple FuturesGroups
    add(contract : String, feed, optional : FuturesFeed)
        adds an individual contract to the group and creates a FuturesFeed, if no feed is provided    
    add_group(group: list)
        adds a group of FuturesFeed to the self.group, creates FuturesFeed from block of FuturesTS
    set_streams(streams : Dictionary, remove, optional : list)
        adds in streams from a dictionary to point to the FuturesFeed, if remove is not None, removes a list 
        of streams from being actively tracked
    remove_feeds(keys : list) 
        deletes the feeds by key from memory storage of self.group and self.active_group
    check(contract : String)
        checks for update of feed of individual FuturesFeed by contract if it is still active
    check_all()
        checks for update of all active contract FuturesFeeds

    """

    def __init__(self, identifiers = [], start_date = None, end_date = None, bar = 'daily', cache = None):
        super().__init__(identifiers, start_date = start_date, end_date = end_date ,cache = cache)
        self.bar_type = bar
        self.not_tradeable = []
        self.__update_group() 

    def __update_group(self):
        if len(self.identifiers) > 0:
            print('Initializing feed with',len(self.identifiers), 'identifiers')
            if len(self.identifiers) > 50:
                for chunk in self.chunk_up(self.identifiers, 50):
                    print('Adding in chunk:',chunk[0],'->', chunk[-1])
                    self.add_group(chunk)
            else:
                self.add_group(self.identifiers)
    

    def _get_feed(self, contract, temp = None):
        feed = SecuritiesFeed(contract, start_date = self.start_date, end_date = self.end_date, bar = self.bar_type) 
        if not temp is None:    
            temp[contract] = feed
        else:
            return feed

    def add(self, contract, feed = None):
        self.group[contract] = self._get_feed(contract) if feed is None else feed
   
    def add_group(self, group):
        if len(group) > 0:
            try:
                df = SecuritiesTS(group, fields = 'open, high, low, close, volume', start_date = self.start_date, end_date = self.end_date, bar = self.bar_type, force_fast = True).data.unstack().dropna().reset_index()
            except:
                df = None

            if df is None:  
                for contract in group:
                    self.not_tradeable.append(contract)
                    print(contract, 'not tradeable')
                return
            if len(group) == 1:
                df.columns = ['field', 'date', 'value']
                df['contract'] = group[0]
            else:
                df.columns = ['contract', 'field', 'date', 'value']
            for contract in group:
                try:
                    self.group[contract] = SecuritiesFeed(contract, bar = self.bar_type, feed = df.loc[df.contract == contract].pivot_table(index = 'date', columns = 'field', values = 'value').to_dict(orient = 'index'), cache = self.cache)
                except:
                    self.not_tradeable.append(contract)
                    print(contract, 'not tradeable')

    def set_streams(self, streams, remove = None):
        new_streams = [x for x in list(streams.keys()) if x not in self.members + self.not_tradeable + list(self.group.keys())]
        if len(new_streams) > 0:
            self.add_group(new_streams)
        for k, s in list(streams.items()):
            if k not in self.not_tradeable:
                if k in list(self.group.keys()):
                    self.active_group[k] = self.group.pop(k)
                self.active_group[k].set_stream(s)
                if k in new_streams:
                    self.active_group[k].check()
        if not remove is None:  
            self.remove_feeds(remove)

    def remove_feeds(self, keys):
        keys = [x for x in keys if x in list(self.group.keys()) + list(self.active_group.keys())]
        for key in keys:
            if key in list(self.group.keys()):
                del self.group[key]
            if key in list(self.active_group.keys()):
                del self.active_group[key]

    def remove_feed(self, key):
        del self.group[key]

    def check(self, key):
        if key in list(self.active_group.keys()):
            self.active_group[key].check()

    def check_all(self):
        for i, f in list(self.active_group.items()):
            f.check()
    
