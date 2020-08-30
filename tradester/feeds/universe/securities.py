from tradester.feeds.active import Price
from tradester.feeds.static import CustomFeed

from .universe import Universe

import pandas as pd


class SecuritiesUniverse(Universe):


    def __init__(self, identifiers, start_date = None, end_date = None, bar = 'daily'):
        super().__init__('SEC', start_date, end_date)
        self.bar = bar
        self.securities_meta_df = self.__get_meta(identifiers)
        self.securities_meta = self.securities_meta_df.set_index('ticker').to_dict(orient = 'index')
        self._streams = {i: Price(bar, contract = i) for i in list(self.securities_meta.keys())}

    @property
    def streams(self):
        return self._streams

    @property
    def tickers(self):
        return list(self.securities_meta.keys())
    
   
    @property
    def info(self):
        return self.securities_meta


    def __get_meta(self, identifiers):
        if isinstance(identifiers, str):
            return CustomFeed(f"select * from securities where {identifiers};").data
        elif isinstance(identifiers, list):
            return CustomFeed(f"select * from securities where ticker in ({str(identifiers).strip('[]')});").data 
        else:
            raise ValueError('The identifiers to a SecuritiesUniverse must be in: [str, list]')
            

    def refresh(self):
        pass
