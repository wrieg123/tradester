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
            for c, asset in universe.assets.items():
                self.add(SMA(asset), (asset.identifier, ))
                #self.add(SMA(asset, period = 80), (asset.identifier, ))
                #self.add(SMA(asset, period = 200), (asset.identifier, ))
    
    def get_trades(self):
        trades = {}
        vs = self.bottom_up.vector_space
        for universe in self.universes.values():
            for contract in universe.tradeable:
                asset = universe.assets[contract]
                sma = vs[contract][-1][0]

                
            
        return trades
        

if __name__ == '__main__':


    universes = [
                FuturesUniverse('Beans', ['BZ'], (1,5)),
                ]
    
    strat = Strat(universes)
    engine = Engine(print_trades = False)
    engine.set_universes(universes)
    engine.set_strategy(strat)
    engine.run()


