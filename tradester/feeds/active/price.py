from .stream import Stream 
import numpy as np

ATTRIBUTES = {
        'minute': ['open','high','low','close','volume','open_interest'],
        'hourly': ['open','high','low','close','volume','open_interest'],
        'daily': ['open','high','low','close','volume','open_interest'],
        'tick': ['b','a', 'bq', 'aq']}

class Price(Stream):
    """
    A Price Stream, controls data handling for various types of input data from bar_type
    
    ...

    Parameters
    ----------
    cache : Integer, None
        how much data to store in memory, if None store all data
    contract : String
        Prices contract as String
    bar_type : String
        type of data to handle, either: minute, hourly, daily, or tick

    Attributes
    ----------
    [ATTRIBUTES]
        attributes are assigned based on bar_type and produces a Stream object for each attribute:
        - minute -> o, h, l, c, vo, oi (open, high, low, close, volume, open interest)
        - hourly -> o, h, l, c, vo, oi (open, high, low, close, volume, open interest)
        - daily -> o, h, l, c, vo, oi (open, high, low, close, volume, open interest)
        - tick -> b, a, bq, aq (bid, ask, bid quantity, ask quantity)
    v : Dictionary
        returns a dictionary of the attribute values from [ATTRIBUTES]
    ts : Dictionary
        returns a dictionary of the attribute time series from [ATTRIBUTES]


    Methods
    -------
    ffill()
        for each attribute, if the attribute is not volume, fill in the previous value
    push(bar : Dictionary) 
        pushes a new dataset onto each attribute

    See Also
    --------
    tradester.feeds.active.Stream

    """
    def __init__(self, bar_type, cache = None, contract = None, multiplier = 1):
        super().__init__(cache)
        self.contract = contract
        self.bar_type = bar_type
        self.attributes = ATTRIBUTES[bar_type]
        for a in ATTRIBUTES[bar_type]:
            setattr(self, a, Stream(cache))

    def __repr__(self):
        return f'<PriceStream ({self.bar_type})>'

    def __str__(self):
        return f'<PriceStream ({self.bar_type})>'
    
    @property
    def market_value(self):
        if self.bar != 'tick':
            if self.close.v is None:
                return None
            else:
                return self.close.v * multiplier


    @property
    def v(self):
        return {a: getattr(self, a).v for a in self.attributes}

    @property
    def ts(self):
        return {a: getattr(self, a).ts for a in self.attributes}
    
    def ffill(self):
        for a in self.attributes:
            if not a in ['volume', 'aq','bq']:
                getattr(self, a).ffill()
            else:
                getattr(self, a).push(0)

    def push(self, bar):
        for a, v in list(bar.items()):
            getattr(self, a).push(v)
