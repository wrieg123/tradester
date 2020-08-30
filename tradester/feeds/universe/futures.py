from tradester.feeds.active import Price
from tradester.feeds.static import CustomFeed

from dateutil.relativedelta import relativedelta as timedelta

from .universe import Universe

import pandas as pd


class FuturesUniverse(Universe):
    """
    A FuturesUniverse if a universe that creates rolling contracts over time by mapping them to continuations
    over time.
    
    ...

    Parameters
    ----------
    products : list
        underlying products of futures to pull in 
    continuation_periods : tuple, optional (default : (1, 12))
        a tuple representing the range in which to create continuous contracts
    start_date : String, optional
        a YYYY-MM-DD representing the start date of the Universe
    end_date :  String, optional
        a YYYY-MM-DD representing the end date of the Universe
    bar : String, optional (default : 'daily')
        type of data to pull in (daily, hourly, minute, tick)
    exchange : String, optional (default : 'CME')
        exchange contracts pulled in are listed on
    
    Attributes
    ----------
    continuations : list
        list of continuation contracts
    continuations_info : Dictionary
        meta data of continuation contracts
    streams : Dictionary
        dictionary of streams and identifier
    inactive_streams : Dictionary
        dictionary of streams where futures contract is no longer active
    active_streams : list
        list of tuples of streams where the futures contract is on the run [(contract, Stream), ...]
    active : list
        list of active contracts
    inactive : list
        list of inactive contracts
    active_info : Dictionary
        dictionary of meta info of active contracts
    
    Methods
    -------
    __get_meta()
        returns meta information of contracts included in the universe, called at class initialization
    __render_active()
        sets the first set of active contracts, called at class intialization
    refresh(reference_date : String, optional)
        refreshes the universe to update the active contracts, passing in refrence data overrides call to
        FeedManager for current date
    
    See Also
    --------
    etl.feeds.active.FeedManager
    etl.feeds.active.Stream
    etl.feeds.static.CustomFeed
    """

    def __init__(self, products, continuation_periods = (1, 12), start_date = None, end_date = None, bar = 'daily', exchange = 'CME'):
        super().__init__('FUT', start_date, end_date)
        self.products = products
        self.bar = bar
        self.exchange = exchange
        self.continuation_periods = continuation_periods 
        self.futures_meta_df = self.__get_meta()
        self.futures_meta = self.futures_meta_df.set_index('contract').to_dict(orient='index')
        self.products_meta = CustomFeed(f'select * from products where product in ({str(products).strip("[]")})').data.set_index('product').to_dict(orient='index')
        self._continuations = CustomFeed(f"select * from futures where product in ({str(products).strip('[]')}) and continuation between {continuation_periods[0]} and {continuation_periods[1]} order by product, continuation asc").data.set_index('contract').to_dict(orient='index') 
        self.mb = None
        self._inactive = {}
        self._streams = {i : Price(bar, contract = i, multiplier = self._continuations[i]['multiplier']) for i in list(self._continuations.keys())}
        self._inactive_streams = {}
        self._active = {}
        self.__render_active() 
    
    def __get_meta(self):
        query = f"select * from futures where product in ({str(self.products).strip('[]')}) and is_continuation = False and daily_start_date is not null"
        if not self.start_date is None:
           query += f" and daily_end_date >= '{self.start_date}'"
        return CustomFeed(query, True, None).data

    def __render_active(self):
        product_to_clearing = {p: c['clearing'] for p, c in self.products_meta.items()}
        for i in self.continuations:    
            self._continuations[i]['reference_contract'] = None
        if self.start_date is None:
            reference_date = min([d[f'{self.bar}_start_date'] for p, d in self.continuations_info.items()])
        else:
            reference_date = self.start_date 
        
        self.refresh(reference_date = reference_date) 

    @property
    def continuations(self):
        return list(self._continuations.keys())

    @property
    def continuations_info(self):
        return self._continuations

    def get_continuation(self, contract):   
        return self._continuations[contract]

    @property
    def streams(self):
        return self._streams

    @property
    def inactive_streams(self):
        return self._inactive_streams
    
    @property
    def active_streams(self):
        return [(k, v) for k, v in list(self.streams.items()) if k in self.active]

    @property
    def active(self):
        return list(self._active.keys())
    
    @property
    def inactive(self):
        return list(self._inactive.keys())

    @property
    def active_info(self):
        return self._active

    def refresh(self, reference_date = None):
        if reference_date is None:  
            reference_date = self.manager.now_date
        front = self.continuation_periods[0]
        back = self.continuation_periods[1]
        mb = pd.to_datetime(reference_date).replace(day = 1).strftime('%Y-%m-%d')
        num_conts = max(back - front, 1)
        self.mb = mb
        max_me = (pd.to_datetime(reference_date) + timedelta(months = back-1) + pd.offsets.MonthEnd(0)).strftime('%Y-%m-%d')
        list_prods = []
        for product in self.products:
            temp = self.futures_meta_df.loc[(self.futures_meta_df.last_trade_date > reference_date) & (self.futures_meta_df.first_trade_date <= reference_date)  & (self.futures_meta_df['product'] == product)].sort_values(['product','soft_expiry'])
            temp['continuation'] = temp.groupby('product').cumcount() + 1
            temp = temp.loc[temp.continuation.between(front,back)]
            temp['clearing'] = temp['product'].apply(lambda x: self.products_meta[x]['clearing'])
            temp['multiplier'] = temp['product'].apply(lambda x: self.products_meta[x]['multiplier'])
            temp['reference_contract'] = temp.apply(lambda x: f"^{x['clearing']}{x['continuation']}", axis = 1)
            list_prods+=temp.head(back).to_dict(orient='records')

        df = pd.DataFrame(list_prods)

        if df.empty:
            return

        references = list(df[['reference_contract']])

        not_in = [i for i in self.continuations if i not in references]
        for i in not_in:    
            self._continuations[i]['reference_contract'] = None
        for r, f in list(df[['reference_contract', 'contract']].set_index('reference_contract').to_dict(orient = 'index').items()):
            self._continuations[r]['reference_contract'] = f['contract']
       
        new = {**self.active_info , **df.set_index('contract').to_dict(orient='index')}
        new = {k: v for k, v in list(new.items()) if not str(v['settlement_date']) in ['None', 'nan']}

        for contract in list(new.keys()): 
            settle = new[contract]['last_trade_date']

            if not settle is None and pd.to_datetime(settle) <= pd.to_datetime(reference_date): 
                if contract in self.streams.keys():
                    self._inactive_streams[contract] = self._streams.pop(contract)
                if contract in self.active:
                    self._inactive[contract] = self._active.pop(contract)
            elif settle is None:
                print('No data', contract) 
            else:
                if not contract in self.active:
                    #print('Adding', contract)
                    self._active[contract] = new[contract]
                    self._streams[contract] = Price(self.bar, contract = contract, multiplier = self.futures_meta[contract]['multiplier'])
