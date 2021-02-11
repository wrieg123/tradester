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

    def __init__(self, name, products, continuation_periods, start_date = None, end_date = None, bar = 'daily', exchange = 'CME', include_continuations = False, include_product = False, roll_on = 'last_trade_date'):
        super().__init__('FUT', name, start_date, end_date)
        self.products = products
        self.continuation_periods = continuation_periods
        self.start_date = start_date
        self.end_date = end_date
        self.bar = bar
        self.exchange = exchange
        self.include_continuations = include_continuations
        self.include_product = include_product
        self.roll_on = roll_on

        self.products_meta = self.__get_products_meta()
        self.futures_meta = self.__get_futures_meta()
        self.calendars, self.calendar_indexes = self.__create_calendar()
        self.continuations_meta = self.__get_continuations_meta()
        self.assets = {k : Future(k, name, bar, v) for k, v in list(self.futures_meta.items()) + list(self.continuations_meta.items())}
        self.tradeable = []
        self.active_list = []
        self.inactive_list = []
        self.active_products = {}
        self.inactive_products = {}

    def __get_products_meta(self):
        """returns information for product information"""

        print("Loading Universe:", self.name, str(self.products).strip('[]'))
        query = f"select * from products where product in ({str(self.products).strip('[]')})"
        return CustomFeed(query).data.set_index('product').to_dict(orient = 'index')

    def __get_futures_meta(self):
        """returns futures meta information"""

        query = f"select * from futures where product in ({str(self.products).strip('[]')}) and is_continuation = False and is_synthetic = False and daily_end_date is not null order by soft_expiry;"
        df = CustomFeed(query).data.set_index('contract')

        if df.dtypes['is_active'] != bool:
            df['is_active'] = df['is_active'].apply(lambda x: x == 1)
            df['is_continuation'] = df['is_continuation'].apply(lambda x: x == 1)
            df['is_synthetic'] = df['is_synthetic'].apply(lambda x: x == 1)

        return df.to_dict(orient = 'index')
   
    def __get_continuations_meta(self):
        """returns the meta information for continuation contracts"""

        return {}
    
    def __create_calendar(self):
        """creates a expiration calendar that rolls contract on the self.roll_on field"""
        
        df = pd.DataFrame(self.futures_meta).T
        df.index.name = 'contract'
        df.reset_index(inplace = True)
        calendars = {}
        indexes = {}

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
            calendars[product] = sub_df[conts].to_dict(orient = 'index')
            index = list(calendars[product].keys())
            index.sort()
            indexes[product] = index
        return calendars, indexes
                    
    def find_date(self, indexes, date, actor = 'active'):
        
        if actor == 'active':
            for i in indexes:
                if i > date:
                    return i
        elif actor == 'inactive':
            for n, i in enumerate(indexes):
                if i >= date:
                    if n >= 1:
                        return indexes[:(n-1)]
                    else:
                        return []


    def refresh(self):
        """ active contracts returned as dict in format: 
            {
                product code: {_product_-_period_: contract, ... },
                ...
            }
        """

        active_products = {}
        inactive_products = {}
        active_list = []
        inactive_list = [] 
        tradeable = [asset.identifier for asset in list(self.assets.values()) if asset.tradeable]
        for product in self.products:
            active_date = self.find_date(self.calendar_indexes[product], self.manager.now)
            active_products[product] = self.calendars[product][active_date]
            
            i_list = []
            for index in self.find_date(self.calendar_indexes[product], self.manager.now, actor = 'inactive'):
                for a in list(self.calendars[product][index].values()):
                    if not self.assets[a].tradeable and a not in list(active_products[product].values()):
                        i_list.append(a)
            
            i_list = list(set(i_list))
            #i_list = list(set(i_list).symmetric_difference(set(list(active_products[product].values()))))
            inactive_products[product] = i_list
            inactive_list.extend(i_list)
            active_list.extend(list(active_products[product].values()))

        if self.include_continuations:
            for product in self.products:
                active_list.extend(list(active_products[product].keys()))
        if self.include_product:
            active_list.extend(self.products)

        self.tradeable = tradeable
        self.active_products = active_products
        self.inactive_products = inactive_products
        self.active_list = active_list
        self.inactive_list = inactive_list

    @property
    def streams(self):
        return {f: s.price_stream for f, s in self.assets.items()}
