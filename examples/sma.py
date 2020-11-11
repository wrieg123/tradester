from tradester import Engine, Indicator, FuturesUniverse, Strategy



class SMA(Indicator):

    def __init__(self, asset, period = 20):
        super().__init__(asset)
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
                self.add(SMA(asset), (asset.identifier, ))
    
    def get_trades(self):
        trades = {}

        indicators = self.bottom_up.get_indicators(assets = self.active_assets)
        positions = self.portfolio.positions

        for universe in self.universes.values():
            for contract in universe.active_list:
                asset = universe.assets[contract]

                try:
                    sma = indicators[contract][:,0][-1] if len(indicators[contract][:,0]) > 0 else 0
                except:
                    sma = 0

                current_position = positions[contract] if contract in positions.keys() else {'units': 0, 'side': 0} 

                if sma > 0:
                    trades[contract] = {
                            'asset': asset,
                            'delta': 10 - current_position['units']*current_position['side'],
                            'order_type': 'TWAP',
                            }
                elif sma < 0:
                    trades[contract] = {
                            'asset': asset,
                            'delta': -10 - current_position['units']*current_position['side'],
                            'order_type': 'TWAP',
                            }
                else:
                    trades[contract] = {
                            'asset': asset,
                            'delta': 0 - current_position['units']*current_position['side'],
                            'order_type': 'TWAP',
                            }

        return trades
        

if __name__ == '__main__':

    universes = [
                FuturesUniverse('Brent', ['BZ'], (1,5)),
                ]
    
    strat = Strat(universes)
    engine = Engine(starting_cash = 1000000, print_trades = False)
    engine.set_universes(universes)
    engine.set_strategy(strat)
    engine.run()

    engine.metrics.plot()
