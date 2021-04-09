from tradester import Engine, Indicator, FuturesUniverse, Strategy
from tradester.utils import MeanStdNormalizer
from tradester.utils.series import get_mean
from time import sleep

import numpy as np


class ATR(Indicator):

    def __init__(self, asset, period, normalizer = None):
        super().__init__(asset, normalizer = normalizer)
        self.period = period
    
    def calculate(self):
        close = self.data.price_stream.close.ts
        high = self.data.price_stream.high.ts
        low = self.data.price_stream.low.ts
        pC = close[:-1]
        
        if len(close) <= 1:
            return 0

        cc = close[1:]
        hc = abs(high[1:] - pC)
        lc = abs(low[1:] - pC)
        hl = high[1:] - low[1:]
        tr = np.maximum(hl, hc, lc)

        return get_mean(tr, self.period)

class Strat(Strategy):
    
    def __init__(self, universes):
        super().__init__(universes)

    def initialize(self):
        for universe in self.universes.values():
            for asset in universe.assets.values():
                self.add(ATR(asset,5, normalizer = None), (asset.identifier, ))

    def trade(self):
        indicators = self.indicators.get_indicators(assets = self.active_assets)

        for universe in self.universes.values():
            for contract in universe.active_list:
                asset = universe.assets[contract]
                atr = indicators[contract][:,0][-1]
                close = asset.price_stream.close.v

                if close is not None:
                    self.oms.place_order(0, asset, 1, order_type = 'MM', bands = {'BID': close - 0.5 * atr, 'ASK': close + 0.5 * atr})

        
if __name__ == '__main__':

    universes = [
                FuturesUniverse('Testing', ['ES'], (1,1)),
                ]
    
    strat = Strat(universes)
    engine = Engine(starting_cash = 1000000, print_trades = False)
    engine.set_universes(universes)
    engine.set_strategy(strat)
    engine.run()

    engine.metrics.plot()
