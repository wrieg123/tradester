from tradester.feeds.factories import SecuritiesFactory, FuturesFactory
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
        master_feed_range = []

        for name, universe in list(self.universes.items()):
            universe.set_manager(self.manager)
            
            if self.bulk_load:
                print('Bulk loading tradeable securities and futures')
                if universe.id_type == 'FUT':
                    self.feed_factories[name] = FuturesFactory(
                               universe.continuations + list(universe.futures_meta.keys()),
                               start_date = self.start_date,
                               end_date = self.end_date,
                               cache = self.cache
                            )
                elif universe.id_type == 'SEC':
                    self.feed_factories[name] = SecuritiesFactory(
                                universe.tickers,
                                start_date = self.start_date,
                                end_date = self.end_date,
                                cache = self.cache
                            )
                self.feed_factories[name].set_streams(universe.streams)
                master_feed_range +=  self.feed_factories[name].feed_range

        self.portfolio._connect(self.manager, self.universes)
        self.oms._connect(self.manager, self.universes)

        master_feed_range = list(set(master_feed_range))
        master_feed_range.sort()

        self.manager.set_calendar(master_feed_range)
        self.manager.set_trading_calendar(master_feed_range)

    def set_strategy(self, strategy):
        self.strategy = strategy
        self.strategy._connect(self.manager, self.oms, self.portfolio)
        self.strategy.initialize()
    
    def run(self, plot = True, fast_forward = False):

        print('Running backtest...')
        print(f'Starting value: ${self.starting_cash:,.0f}')
        cont = True
        start = time.time()

        if self.progress_bar:
            pbar = tqdmr(total = len(self.manager.calendar), ascii = True)

        while cont:
            now = time.time()
            self.manager.update()

            if self.manager.now != 'END':
                if self.print_trades:
                    print()
                    print('-----', self.manager.now, '-----')

                    for _, factory in list(self.feed_factories.items()):
                        factory.check_all()
                    for name, universe in list(self.universes.items()):
                        universe.refresh()
                        if universe.id_type == 'FUT':
                            self.feed_factories[name].set_streams(universe.streams,  remove = universe.inactive)
                        else:
                            self.feed_factories[name].set_streams(universe.streams)
                    
                    self.oms.process()
                    self.portfolio.reconcile()

                    self.strategy.refresh()

                    if self.print_trades:
                        print(f'Portfolio Value: ${self.portfolio.value:,.0f}')

                    if not fast_forward:
                        self.strategy.trade()
                    if self.progress_bar:
                        pbar.set_description(f"Portfolio Value: ${self.portfolio.value:,.0f}")

            else:
                cont = False
            if self.progress_bar:
                pbar.update(1)
        if self.progress_bar:
            pbar.close()
        print('Total Time:', round((time.time() - start)/60, 2), 'minutes')

        if plot:
            self.metrics._print()
            self.metrics.plot()
