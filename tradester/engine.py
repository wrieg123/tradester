from tradester.finance.factories import SecuritiesFactory, FuturesFactory, ClockManager, Worker

from .portfolio import Portfolio
from .metrics import Metrics
from .oms import OMS

from tqdm import tqdm as tqdmr

import pandas as pd
import time


class Engine():
    """
    The main engine of the backtest.

    ...
    
    Parameters
    ----------
    starting_cash : int
        starting cash balance
    start_date : string (YYYY-MM-DD)
        date at which to start trading, might not be all available data; see Universes
    end_date : string (YYYY-MM-DD)
        date at which to end trading
    bulk_load : boolean
        bulk load the data (or not if False)
    adv_participation : float
        see OMS
    adv_period : int
        see OMS
    adv_oi : int
        see OMS
    progress_bar : boolean
        show the progress bar
    print_trades : boolean
        print out the trades (turns progress bar off)
    
    Attributes
    ----------
    manager : tradester.factories.Worker.manager
        the central manager for all Workers, construction method exploits memory management of python
    universes : dict
        dictionary of all tradeable universes, format : {'name' : tradester.finance.Universe, ... }
    feed_factories : dict
        dictionary of all feed factories associated with universes, format : {'name': tradester.factories.FeedFactory, ... }
    portfolio : tradester.portfolios.Portfolio
        central portfolio object
    oms : tradester.oms.OMS
        central order management system
    metrics : tradester.Metrics
        class for metrics
    strategy : tradester.strategy.Strategy
        user-defined strategy

    Methods
    -------
    set_universes(universes : list)
        sets the self.universes attribute and connects the oms, portfolio and universes together and to the central manager (self.manager)
    set_strategy(strategy : tradester.strategy.Strategy)
        sets the user defined strategy and connects it to the portfolio, oms and manager


    """
    def __init__(
            self, 
            starting_cash = 1000000, 
            start_date = None, 
            end_date = None, 
            bulk_load = True, 
            cache = None, 
            adv_participation = .1, 
            adv_period = 21, 
            adv_oi = 0.05, 
            progress_bar = True, 
            print_trades = False, 
            ):
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

        self.manager = Worker(None).manager
        self.universes = {} 
        self.feed_factories = {}
        self.portfolio = Portfolio(starting_cash, print_trades = print_trades)
        self.oms = OMS(adv_participation = adv_participation, adv_period = adv_period, adv_oi = adv_oi)
        self.metrics = Metrics(self.portfolio, self.oms, start_date, end_date)
        self.strategy = None


    def set_universes(self, universes):
        self.universes = {u.name : u for u in universes}
        master_feed_range = []

        for universe in self.universes.values():
            name = universe.name
            universe.set_manager(self.manager)
            
            if self.bulk_load:
                print('Bulk loading tradeable securities and futures')
                if universe.id_type == 'FUT':
                    self.feed_factories[name] = FuturesFactory(
                               list(universe.assets.keys()),
                               start_date = self.start_date,
                               end_date = self.end_date,
                               cache = self.cache
                            )
                elif universe.id_type == 'SEC':
                    self.feed_factories[name] = SecuritiesFactory(
                                list(universe.assets.keys()),
                                start_date = self.start_date,
                                end_date = self.end_date,
                                cache = self.cache
                            )
                self.feed_factories[name].set_streams(universe.streams)
                master_feed_range +=  self.feed_factories[name].feed_range

        self.portfolio._connect(self.manager)
        self.oms._connect(self.manager, self.portfolio)

        master_feed_range = list(set(master_feed_range))
        master_feed_range.sort()
        self.manager.set_calendar(master_feed_range)
        self.manager.set_trading_calendar(master_feed_range)

    def set_strategy(self, strategy):
        self.strategy = strategy
        self.strategy._connect(self.manager, self.oms, self.portfolio)
        self.strategy.initialize()
    
    def run(self, fast_forward = False, metrics = True):

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

                tradeable_assets = []
                for name, universe in list(self.universes.items()):
                    universe.refresh()
                    tradeable = universe.tradeable
                    self.feed_factories[name].set_active(tradeable)
                    for asset in tradeable:
                        tradeable_assets.append(asset)
                
                self.oms.process()
                self.portfolio.reconcile()

                self.strategy.refresh(tradeable_assets)

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

        if metrics:
            self.metrics._calculate()

            self.metrics.print()
