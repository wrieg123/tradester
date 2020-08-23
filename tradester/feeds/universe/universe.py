from etl.feeds.static import CustomFeed
from etl.utils import contract_months, contract_months_l

from dateutil.relativedelta import relativedelta as timedelta

from .futures import Future

import pandas as pd
import math

__all__ = ['FuturesUniverse']

class Universe():
    """
    A Universe is the fundamental storage device for tradeable contracts.
    
    ...

    Parameters
    ----------
    start_date : String
        a YYYY-MM-DD representing the start date of the Universe
    end_date :  String
        a YYYY-MM-DD representing the end date of the Universe
    
    Methods
    -------
    set_start_date(date : String)
        sets self.start_date
    set_end_Date (date : String)
        sets self.end_date
    set_manager(manager : FeedManager)
        sets self.manager
    
    See Also
    --------
    etl.feeds.active.FeedManager
    """

    def __init__(self, id_type, start_date, end_date):
        self.manager = None 
        self.id_type = id_type
        self.start_date = start_date 
        self.end_date = end_date
    
    def set_start_date(self, date):
        self.start_date = date
    
    def set_end_date(self, date):
        self.end_date = date

    def set_manager(self, manager):
        self.manager = manager 
