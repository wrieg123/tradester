from tradester.feeds.active import Price

import pandas as pd

class Asset():
    """
    A tradeable asset.

    ...

    Parameters
    ----------
    id_type : str
        type of asset
    identifier : str
        identifier
    bar : str
        time series
    meta : dict
        meta information
    """

    def __init__(self, id_type, identifier, universe, bar, meta, tradeable_override = False):
        self.id_type = id_type
        self.identifier = identifier
        self.universe = universe
        self.bar = bar
        self.meta = meta
        self.tradeable_override = tradeable_override
        self.price_stream = Price(bar, cache = None, contract = identifier, multiplier = meta['multiplier'] if 'multiplier' in meta.keys() else 1)
        self.manager = None
        self.start_date = pd.to_datetime(meta['daily_start_date']) if 'daily_start_date' in meta.keys() and meta['daily_start_date'] is not None else pd.to_datetime('2050-01-01') 
        self.end_date = pd.to_datetime(meta['daily_end_date']) if 'daily_end_date' in meta.keys() and meta['daily_end_date'] is not None else pd.to_datetime('1960-01-01') 
        self.last_trade_date = pd.to_datetime(meta['last_trade_date']) if 'last_trade_date' in meta.keys() and meta['last_trade_date'] is not None else None 

    @property
    def tradeable(self):
        if self.tradeable_override:
            return True
        return self.start_date <= self.manager.now and self.manager.now < self.end_date

    def set_manager(self, manager):
        self.manager = manager
