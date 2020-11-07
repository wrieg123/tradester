from tradester.feeds.static import CustomFeed
from tradester.finance.assets import Future

from .universe import Universe

import pandas as pd



class FuturesUniverse(Universe):
    """
    A universe of tradeable futures contracts.

    ...

    Parameters
    ----------
    name : str
        name of the universe
    products : list
        underlying products of futures to trade
    continuation_periods : tuple (ex : (1, 12))
        a tuple representing the range in which to create continuous contracts
    start_date : String, optional
        a YYYY-MM-DD representing the start date of the Universe
    end_date :  String, optional
        a YYYY-MM-DD representing the end date of the Universe
    bar : String, optional (default : 'daily')
        type of data to pull in (daily, hourly, minute, tick)
    exchange : String, optional (default : 'CME')
        exchange contracts pulled in are listed on
    include_continuations : Boolean, optional (default : False)
        include continuation contracts
    include_synthetics : Boolean, optional (default : False)
        include synthetic continuation contracts
    roll_on : String, optional (default : 'last_trade_date')
        date for which to roll contracts on
    
    Attributes
    ----------
    futures_meta : dict
        meta information of futures contracts
    products_meta : dict
        meta information of products

    """

    def __init__(self, name, products, continuation_periods, start_date = None, end_date = None, bar = 'daily', exchange = 'CME', include_continuations = False, include_synthetics = False, roll_on = 'last_trade_date'):
        super().__init__('FUT', name, start_date, end_date)
        self.products = products
        self.continuation_periods = continuation_periods
        self.start_date = start_date
        self.end_date = end_date
        self.bar = bar
        self.exchange = exchange
        self.include_continuations = include_continuations
        self.include_synthetics = include_synthetics
        self.roll_on = roll_on

        self.products_meta = self.__get_products_meta()
        self.futures_meta = self.__get_futures_meta()
        self.calendars = self.__create_calendar()
        self.continuations_meta = self.__get_continuations_meta()
        self.assets = {k : Future(k, name, bar, v) for k, v in list(self.futures_meta.items()) + list(self.continuations_meta.items())}
        self.tradeable = []
        self.active_products = {}
        self.inactive_products = {}

    def __get_products_meta(self):
        """returns information for product information"""

        query = f"select * from products where product in ({str(self.products).strip('[]')})"
        return CustomFeed(query).data.set_index('product').to_dict(orient = 'index')

    def __get_futures_meta(self):
        """returns futures meta information"""

        query = f"select * from futures where product in ({str(self.products).strip('[]')}) and is_continuation = False and is_synthetic = False"
        df = CustomFeed(query).data.set_index('contract')

        if df.dtypes['is_active'] != bool:
            df['is_active'] = df['is_active'].apply(lambda x: x == 1)
            df['is_continuation'] = df['is_continuation'].apply(lambda x: x == 1)
            df['is_synthetic'] = df['is_synthetic'].apply(lambda x: x == 1)

        return df.to_dict(orient = 'index')
   
    def __get_continuations_meta(self):
        """returns the meta information for continuation contracts"""

        if self.include_continuations or self.include_synthetics:
            if self.include_continuations and self.include_synthetics:
                query = f"select * from futures where product in ({str(self.products).strip('[]')}) and is_continuation = True order by soft_expiry asc"
            else:
                query = f"select * from futures where product in ({str(self.products).strip('[]')}) and is_continuation = True and is_synthetic = {self.include_synthetics} order by soft_expiry asc"
            df = CustomFeed(query).data.set_index('contract')

            if df.dtypes['is_active'] != bool:
                df['is_active'] = df['is_active'].apply(lambda x: x == 1)
                df['is_continuation'] = df['is_continuation'].apply(lambda x: x == 1)
                df['is_synthetic'] = df['is_synthetic'].apply(lambda x: x == 1)
        else:
            return {}
    
    def __create_calendar(self):
        """creates a expiration calendar that rolls contract on the self.roll_on field"""
        
        df = pd.DataFrame(self.futures_meta).T
        df.index.name = 'contract'
        df.reset_index(inplace = True)
        calendars = {}

        for product in self.products:
            sub_df = df.loc[df['product'] == product].copy()
            sub_df = sub_df[['contract', self.roll_on]].set_index(self.roll_on)
            sub_df.index = pd.to_datetime(sub_df.index)
            sub_df.sort_index(inplace = True)
            sub_df.columns = [f'{product}-1']
            conts = []

            for i in range(self.continuation_periods[0], self.continuation_periods[1] + 1):
                s_factor = i - 1
                cont = f'{product}-{i}'
                conts.append(cont)

                if s_factor != 0:
                    sub_df[cont] = sub_df[f'{product}-1'].shift(-s_factor)
            
            calendars[product] = sub_df[conts]
        return calendars
                    
    def refresh(self):
        """ active contracts returned as dict in format: 
            {
                product code: {_product_-_period_: contract, ... },
                ...
            }
        """

        active_products = {}
        inactive_products = {}
        for product in self.products:
            active_products[product] = self.calendars[product].loc[self.calendars[product].index > self.manager.now].head(1).to_dict(orient = 'records')[0]
            #inactive_list = list(set(list(self.calendars[product].loc[self.calendars[product].index < self.manager.now].tail(-1).values.flatten())))
            #inactive_products[product] = [x for x in inactive_list if x not in active_products[product].values()]

        tradeable = []
        for asset in self.assets.values():
            if asset.tradeable:
                tradeable.append(asset.identifier)

        self.tradeable = tradeable 
        self.active_products = active_products
        self.inactive_products = inactive_products

    @property
    def streams(self):
        return {f: s.price_stream for f, s in self.assets.items()}
