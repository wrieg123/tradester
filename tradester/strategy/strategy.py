from tradester.feeds.active import IndicatorGroup, Stream

from .signal import Signal, SignalGroup



class Strategy():

    def __init__(self, universes : dict):
        self.universes = universes
        self.manager = None
        self.oms = None
        self.portfolio = None
        self.top_down = {
                'G': IndicatorGroup(group_type = 'dict'),
                'L': IndicatorGroup(group_type = 'dict'),
                'R': IndicatorGroup(group_type = 'dict')
                }
        self.bottom_up = SignalGroup()
        
    def _connect(self, manager, oms, portfolio):
        self.manager = manager
        self.oms = oms
        self.portfolio = portfolio
    
    def _refresh(self):
        for i in list(self.top_down.values()):
            i.refresh()
        self.bottom_up.refresh()

    def add(self, indicator, identifiers, base = 'bottom_up', group = None, name = None):
        if base == 'bottom_up':
            self.bottom_up._add(Signal(indicator, identifiers, grouping = group))
        elif base == 'top_down':
            self.top_down[group].add(indicator, name = name)


    def initialize(self):
        raise NotImplementedError("You must implement a self.initialize() method")
    

    def trade(self):
        get_trades = getattr(self, 'get_trades', None)
        if not callable(get_trades):
            raise NotImplementedError("You must implement a self.get_trades() method, if you do not define your own trade method")
        trades = self.get_trades()
        positions = self.portfolio.positions

        for c, info in list(trades.items()):
            id_type = info['id_type']
            universe = info['universe']
            delta = info['delta']

            if delta != 0 and not c is None:
                self.oms.place_order(1 if delta > 0 else -1, id_type, c, abs(delta), universe)
