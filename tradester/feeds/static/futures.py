from .feed import MetaFeed, TSFeed 

__all__ = ['FuturesMeta', 'FuturesTS']
        
class FuturesMeta(MetaFeed):

    def __init__(self, identifiers, credentials = None):
        super().__init__(identifiers, "*", "futures", "contract", credentials)

class FuturesTS(TSFeed):

    def __init__(self, identifiers, fields = 'open, high, low, close, volume', start_date = None, end_date = None, bar = 'daily', credentials = None, force_fast = True):
        super().__init__(identifiers, fields, "futures", "contract", credentials, bar, start_date, end_date, force_fast = force_fast)
