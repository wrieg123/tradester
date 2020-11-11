from tradester.feeds.static import FuturesTS
from .worker import Worker, WorkerGroup

from multiprocessing import Process, Pool, Manager
from copy import deepcopy
from time import sleep
import pandas as pd

class FuturesWorker(Worker):
    """
    A FuturesWorker is a child of parent, Worker, which is build specifically to handle futures contracts.
    
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

    """
    
    def __init__(self, contract, start_date = None, end_date = None, bar = 'daily', feed = None, cache = None):
        super().__init__(contract, start_date = start_date, end_date = end_date, feed = feed, cache= cache)
        self.bar_type = bar
        self.__check_feed()
    
    def __repr__(self):
        return f'<FuturesWorker {self.identifier} ({self.start_date.strftime("%Y-%m-%d")} -> {self.end_date.strftime("%Y-%m-%d")})>'

    def __check_feed(self):
        if self.feed is None:
            self.feed = FuturesTS(self.identifier, fields = 'open, high, low, close, volume, open_interest', start_date = self.start_date, end_date = self.end_date, bar = self.bar_type).data.to_dict(orient= 'index')

        if self.start_date is None:
            self.start_date = min(self.feed.keys())
        if self.end_date is None:
            self.end_date = max(self.feed.keys())


class FuturesFactory(WorkerGroup):
    """
    A FuturesGroup is a WorkerGroup built to handle futures contracts.
    
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
        upon class initialization, add in the identifier FuturesWorker objects
    _get_feed(contract : String, temp, optional : dictionary):
        returns Worker object within self.group at contract, if temp is passed in; handles support for pooling
        of multiple FuturesGroups
    add(contract : String, feed, optional : FuturesWorker)
        adds an individual contract to the group and creates a FuturesWorker, if no feed is provided    
    add_group(group: list)
        adds a group of FuturesWorker to the self.group, creates FuturesWorker from block of FuturesTS
    set_streams(streams : Dictionary, remove, optional : list)
        adds in streams from a dictionary to point to the FuturesWorker, if remove is not None, removes a list 
        of streams from being actively tracked
    remove_feeds(keys : list) 
        deletes the feeds by key from memory storage of self.group and self.active_group
    check(contract : String)
        checks for update of feed of individual FuturesWorker by contract if it is still active

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
                manager = Manager()
                holder = manager.list()
                pool = Pool(processes = 4)
                for group in self.chunk_up(self.identifiers, 50):
                    pool.apply_async(self.add_group, args = [group, holder])
                pool.close()
                pool.join()

                master_df = pd.concat(holder)

                available = list(master_df['contract'].unique())
                tradeable = set(self.identifiers).intersection(set(available))
                self.not_tradeable = list(set(available).symmetric_difference(set(self.identifiers)))

                grouped = dict(tuple(master_df.groupby('contract')))
                print('Not Tradeable:', self.not_tradeable)
                for contract in tradeable:
                    self.group[contract] = FuturesWorker(contract, bar = self.bar_type, feed = grouped[contract].pivot_table(index = 'date', columns = 'field', values = 'value').to_dict(orient = 'index'), cache = self.cache)


            else:
                self.add_group(self.identifiers, None)
    

    def _get_feed(self, contract, temp = None):
        feed = FuturesWorker(contract, start_date = self.start_date, end_date = self.end_date, bar = self.bar_type) 
        if not temp is None:    
            temp[contract] = feed
        else:
            return feed

    def add(self, contract, feed = None):
        self.group[contract] = self._get_feed(contract) if feed is None else feed
   
    def add_group(self, group, holder):
        print('Adding in group:',group[0],'->', group[-1])
        sleep(1)
        if len(group) > 0:
            try:
                df = FuturesTS(group, fields = 'open, high, low, close, volume, open_interest', start_date = self.start_date, end_date = self.end_date, bar = self.bar_type, force_fast = True).data.unstack().dropna().reset_index()
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
            if not holder is None:
                holder.append(df)
            else:
                for contract in group:
                    try:
                        self.group[contract] = FuturesWorker(contract, bar = self.bar_type, feed = df.loc[df.contract == contract].pivot_table(index = 'date', columns = 'field', values = 'value').to_dict(orient = 'index'), cache = self.cache)
                    except:
                        self.not_tradeable.append(contract)
                        print(contract, 'not tradeable')

    def set_streams(self, streams):
        for k, s in list(streams.items()):
            if k not in self.not_tradeable:
                self.group[k].set_stream(s)
