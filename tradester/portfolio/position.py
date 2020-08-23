

class Position():

    def __init__(self, stream, id_type, identifier, multiplier, side, units, cost_basis, universe):
        self.stream = stream
        self.id_type = id_type
        self.identifier = identifier
        self.multiplier = multiplier
        self.side = self.side
        self.units = units
        self.cost_basis = cost_basis
        self.universe = universe
    
    @property
    def market_value(self):
        return self.units * self.stream.market_value.v * self.side

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
            'last': self.stream.close.v,
            'universe': self.universe,
        }

