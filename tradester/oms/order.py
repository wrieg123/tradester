

class Order():
    
    def __init__(self, num, order_type, asset, side, units, entry_date, entry_price, time_in_force = None, bands = {}, fok = False):
        self.status = 'PLACED'
        self.num = num
        self.order_type = order_type
        self.asset = asset
        self.id_type = asset.id_type
        self.identifier = asset.identifier
        self.side = side
        self.units = units
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.time_in_force = time_in_force
        self.bands = bands
        self.fok = fok
        self.fill_price = None
        self.fill_date = None
        self.fill_units = 0
        self.cancel_date = None
        self.update_date = None
        self.days_on = 0
    
    @property
    def info(self):
        return {
            'status': self.status,
            'num': self.num,
            'order_type': self.order_type,
            'id_type': self.id_type,
            'identifier': self.identifier,
            'side': self.side,
            'units': self.units,
            'entry_date': self.entry_date,
            'entry_price': self.entry_price,
            'time_in_force': self.time_in_force,
            'bands': self.bands,
            'fok': self.fok,
            'fill_units': self.fill_units,
            'fill_price': self.fill_price,
            'fill_date' : self.fill_date,
            'cancel_date': self.cancel_date,
            'days_on': self.days_on,
            'time_in_force': self.time_in_force,
            'update_date': self.update_date,
        }

    def bump(self):
        self.days_on += 1
    
    def cancel(self, date):
        self.status = 'CANCELLED'
        self.cancel_date = date
    
    def update(self, date):
        self.status = 'UPDATED'
        self.update_date = date

    def fill(self, date, price, partial):
        self.status = 'FILLED' if partial == self.units else 'PARTIAL'
        self.fill_date = date
        self.fill_price = price
        self.fill_units = partial
