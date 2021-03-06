from tradester import Engine, Indicator, FuturesUniverse, Strategy
from tradester.utils import MeanStdNormalizer
from time import sleep



class SMA(Indicator):

    def __init__(self, asset, period = 20, normalizer= None):
        super().__init__(asset, normalizer = normalizer)
        self.period = period
    
    def calculate(self):
        data = self.data.price_stream.close.ts

        if len(data) < self.period:
            return 0
        
        return data[-1] / data[-self.period:].mean() - 1


class Strat(Strategy):
    
    def __init__(self, universes):
        super().__init__(universes)

    
    def initialize(self):
        for universe in self.universes.values():
            for asset in universe.assets.values():
                self.add(SMA(asset, normalizer = None), (asset.identifier, ))
    
    def get_trades(self):
        trades = {}

        indicators = self.indicators.get_indicators(assets = self.active_assets)

        for universe in self.universes.values():
            for contract in universe.active_list:
                asset = universe.assets[contract]

                try:
                    sma = indicators[contract][:,0][-1] if len(indicators[contract][:,0]) > 0 else 0
                except:
                    sma = 0

                current_position = self.portfolio.get_position(contract)

                if sma > 0:
                    trades[contract] = {
                            'asset': asset,
                            'delta': 10 - current_position['units']*current_position['side'],
                            'order_type': 'BEST_FILL',
                            }
                elif sma < 0:
                    trades[contract] = {
                            'asset': asset,
                            'delta': -10 - current_position['units']*current_position['side'],
                            'order_type': 'BEST_FILL',
                            }
                else:
                    trades[contract] = {
                            'asset': asset,
                            'delta': 0 - current_position['units']*current_position['side'],
                            'order_type': 'BEST_FILL',
                            }

        return trades
        

if __name__ == '__main__':

    universes = [
                FuturesUniverse('Brent', ['BB'], (1,1)),
                ]
    
    strat = Strat(universes)
    engine = Engine(starting_cash = 1000000, print_trades = False)
    engine.set_universes(universes)
    engine.set_strategy(strat)
    engine.run()

    engine.metrics.plot()
