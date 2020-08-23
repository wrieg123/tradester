from tradester.feeds.active import Feed

from .portfolio import Portfolio
from .metrics import Metrics
from .oms import OMS

from tqdm import tqdm as tqdmr

import pandas as pd
import time


class Engine():

    def __init__(self, starting_cash = 10000000, start_date = None, end_date = None, bulk_load = True, cache = None, adv_participation = .2, adv_period = 21, adv_oi = 0.05, progress_bar = True, print_trades = False, trade_start_date = None):
        self.starting_cash = starting_cash
        self.start_date = start_date
        self.end_date = end_date
        self.bulk_load = bulk_load
        self.cache = cache
        self.adv_participation = adv_participation
        self.adv_period = adv_period
        self.adv_oi = adv_oi
        self.progress_bar = progress_bar if print_trades == False else False
        self.print_trades = print_trades
        self.trade_start_date = trade_start_date
        self.universes = {}
        self.feed_factories = {}
        self.portfolio = Portfolio(starting_cash, print_trades = print_trades)
        self.oms = OMS(self.portfolio, adv_participation = adv_participation, adv_period = adv_period, adv_oi = adv_oi)
        self.metrics = Metrics(self.portfolio, trade_start_date = trade_start_date)
        self.strategy = None

    def set_universes(self, universes):
        self.universes = universes
        for _, universe in list(self.universes.items()):
            universe.set_manager(self.manager)

        self.portfolio._connect(self.manager, self.universes)
        self.oms._connect(self.manager, self.universes)

        if self.bulk_load:
            print('Bulk loading contracts')


