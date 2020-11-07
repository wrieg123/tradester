

class Position():

    def __init__(self, asset, side, units, cost_basis):
        self.asset = asset
        self.id_type = asset.id_type
        self.identifier = asset.identifier
        self.multiplier = asset.price_stream.multiplier
        self.side = side
        self.units = units
        self.cost_basis = cost_basis
    
    @property
    def market_value(self):
        return self.units * self.asset.price_stream.market_value * self.side

    @property
    def pnl(self):
        return self.market_value - self.cost_basis

    @property
    def avg_px(self):
        return self.cost_basis / self.multiplier / self.units
    
    @property
    def info(self):
        return {
            'id_type': self.id_type,
            'identifier': self.identifier,
            'side': self.side,
            'multiplier': self.multiplier,
            'units': self.units,
            'cost_basis': self.cost_basis,
            'market_value': self.market_value,
            'pnl': self.pnl,
            'avg_px': self.avg_px,
            'last': self.asset.price_stream.close.v,
        }

