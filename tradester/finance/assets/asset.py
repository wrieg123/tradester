from tradester.feeds.active import Price

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

    def __init__(id_type, identifier, universe, bar, meta):
        self.id_type = id_type
        self.identifier = identifier
        self.universe = universe
        self.bar = bar
        self.meta = meta
        self.price_stream = Price(bar, 
                                 cache = None, 
                                 contract = identifier, 
                                 multiplier = meta['multiplier'] if 'multiplier' in meta.keys() else 1,
                                 )
