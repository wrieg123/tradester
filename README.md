# Tradester
Tradester is a python-based backtesting framework to test trading strategies using futures and equities. The current implementation is meant to interface with the data infrastructure I currently have set up.


## Setup

```
py setup.py install
```

## Running a Strategy (SMA Strategy)
```
from tradester.feeds.universe import FuturesUniverse, SecuritiesUniverse
from tradester.feeds.active import Indicator
from tradester.strategy import Strategy
from tradester import Engine


class SMA(Indicator):
  def __init__(self, data, period = 200):
    super().__init__(data, None)
   
  def calculate(self, data):
    if len(data) < self.period:
      return 0
    
    return data[-1] / data[-self.period:].mean() -1 #show sma as % of close
 
 
class FakeStrat(Strategy):
  def __init__(self, universes):
    super().__init__(universes)
   
  
  def initialize(self): # default method, add indicators to stack
    for ticker in self.universes['equities'].tickers:
      self.add(SMA(self.universes['equities'].streams[ticker].close, period = 200), [ticker])
  
  def get_trades(self): # default method, return dict of trades
    positions = self.portfolio.positions
    value = self.portfolio.value
    
    full_vs = self.bottom_up.full_vector_space
    trades = {}
    for ticker in self.universes['equities'].tickers:
      sma = full_vs[ticker]['None']['SMA'][:,0][-1] # get last sma value
      current_shares = positions[ticker]['units'] * positions[ticker]['side'] if ticker in positions.keys() else 0
      mv = self.universes['equities'].streams[ticker].market_value
      
      if v > 0:
        cw = 1/len(self.universes['equities'].tickers) # 1/N weighting
      elif v < 0:
        cw = -1/len(self.universes['equities'].tickers) # 1/N weighting
      else:
        cw = 0
      tgt_shares = int((cw * value) / mv))
      trades[ticker] = {
        'id_type': 'SEC', # type of ticker is security
        'universe': 'equities',
        'delta': tgt_shares - current_shares,
      }
      
      
  return trades




if __name__ == '__main__':
  START_DATE = '2000-01-01'
  universes = {
    'equities': SecuritiesUniverse(['SPY'], start_date = START_DATE),
    'futures': FuturesUniverse(['VX'], continuation_periods = (1,4), start_date = START_DATE), # included for example, but not traded
  }

  strat = FakeStrat(universe) #tradester.strategy.Strategy object
  engine = Engine()
  engine.set_universes(universes)
  engine.set_strategy(strat)

  engine.run()
```
