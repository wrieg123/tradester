

class Order():
    """
    An order object that gets used by OMS

    ...

    Parameters
    ----------
    num : int
        Order number
    order_type : string
        order type
    asset : tradester.finance.Asset
        asset associated with order
    side : int, either 1 or -1
        side of order (1 for buy, -1 sell)
    units : int
        number of units to trade
    entry_date : datetime
        datetime of trade entry
    entry_price : float
        closing price of asset when trade is entered (day 0)
    time_in_force : int, optional
        number of days the trade remains on the order book, indefinite if None
    bands : dict
        any bands to be associated with the trade
    fok : boolean, optional (default : False)
        fill or kill, if the order doesn't get filled the next turn, kill the order

    Attributes
    ----------
    fill_price : float
        price the trade gets filled at
    fill_date : datetime
        datetime the trade gets filled at
    filled_units : int
        how many units get filled
    cancel_date : datetime
        datetime of order cancelation
    update_date : datetime
        datetime of order update
    days_on : int
        number of days the order has been on the order book
    info : dict
        takes all necessary attributes and returns them as a dictionary
    
    Methods
    -------
    bump()
        increments days_on
    cancel(date : datetime)
        cancel the order
    update(date : datetime)
        updates the order, usually a new order gets placed
    fill(date : datetime, price : float, partial : int)'
        marks the order as filled (or partially filled) and sets the fill_price
    
    """
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
