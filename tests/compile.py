from tradester import Engine, Indicator, FuturesUniverse, Strategy


class Strat(Strategy):
    
    def __init__(self, universes):
        super().__init__(universes)

    
    def initialize(self):

        pass

if __name__ == '__main__':


    universes = [
            FuturesUniverse('Milk', ['DA'], (1,5)),

            ]
    
    strat = Strat(universes)
    engine = Engine()
    engine.set_universes(universes)
    #engine.run()


