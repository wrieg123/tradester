from tradester.feeds.active import IndicatorGroup, Stream

from .signal import Signal, SignalGroup



class Strategy():

    def __init__(self, universes):
        self.universes = {u.name : u for u in universes}
        self.manager = None
        self.oms = None
        self.portfolio = None
        self.top_down = { }
        self.covariance_map = { }
        self.indicators = SignalGroup()
    
    @property
    def active_assets(self):
        assets = []
        for u in self.universes.values():
            for a in u.active_list:
                assets.append(a)
        return assets
    
    @property
    def tradeable_assets(self):
        assets = []
        for u in self.universes.values():
            for a in u.tradeable:
                assets.append(a)
        return assets

    @property
    def inactive_assets(self):
        assets = []
        for u in self.universes.values():
            for a in u.inactive_list:
                assets.append(a)
        return assets

    def _connect(self, manager, oms, portfolio):
        self.manager = manager
        self.oms = oms
        self.portfolio = portfolio
    
    def refresh(self, assets):
        for i in list(self.top_down.values()):
            i.refresh()
        for i in list(self.covariance_map.values()):
            i.refresh()
        self.indicators.refresh(assets = assets)

    def add(self, indicator, identifiers, base = 'indicators', group = None, name = None):
        if base == 'indicators':
            self.indicators._add(Signal(indicator, identifiers, grouping = group, name = name))
        elif base == 'top_down':
            if not group in self.top_down.keys():
                self.top_down[group] = IndicatorGroup(group_type = 'dict')
            self.top_down[group].add(indicator, name = name)
        elif base == 'covariance':
            if not name in self.covariance_map.keys():
                self.covariance_map[name] = SignalGroup()
            self.covariance_map[name]._add(Signal(indicator, identifiers, grouping = group))

    def initialize(self):
        raise NotImplementedError("You must implement a self.initialize() method")

    def trade(self):
        get_trades = getattr(self, 'get_trades', None)
        if not callable(get_trades):
            raise NotImplementedError("You must implement a self.get_trades() method, if you do not define your own trade method")
        trades = self.get_trades()
        positions = self.portfolio.positions

        for c, info in list(trades.items()):
            asset = info['asset']
            delta = info['delta']
            order_type = info['order_type'] if 'order_type' in info.keys() else 'MARKET'
            bands = info['bands'] if 'bands' in info.keys() else {}
            fok = info['fok'] if 'fok' in info.keys() else False

            if delta != 0 and not c is None:
                self.oms.place_order(1 if delta > 0 else -1, asset, abs(delta), order_type = order_type, bands = bands, fok = fok)
