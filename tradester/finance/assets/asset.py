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

    def __init__(self, id_type, identifier, universe, bar, meta):
        self.id_type = id_type
        self.identifier = identifier
        self.universe = universe
        self.bar = bar
        self.meta = meta
        self.price_stream = Price(bar, cache = None, contract = identifier, multiplier = meta['multiplier'] if 'multiplier' in meta.keys() else 1)
        self.manager = None
        self.start_date = pd.to_datetime(meta['daily_start_date']) if meta['daily_start_date'] is not None else None
        self.end_date = pd.to_datetime(meta['daily_end_date']) if meta['daily_end_date'] is not None else None
    
    @property
    def tradeable(self):
        if self.start_date is None or self.end_date is None:
            return False
        else:
            return self.start_date <= self.manager.now <= self.end_date

    def set_manager(self, manager):
        self.manager = manager
