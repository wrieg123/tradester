from .order import Order


STANDARD_FEES = {
    'FUT': 3.00,
    'SEC': 0.01,
}

class OMS():
    """
    The Order Management System (OMS) is meant to the point of contact between a user defined strategy
    and the portfolio. A strategy places orders, and whether or not that order gets filled puts the assets
    into the portfolio.

    ...

    Paramaters
    ----------
    adv_participation : float, optional (default : .10)
        percentage of average daily volume for the asset traded
    adv_period : float, optional (default : 21)
        days for which to calculate average daily volume
    adv_oi : float, optional (default : 0.05)
        percentage of open interested to trade with
    fee structure : dict, optional
        fee structure for asset types to calculate trading comissions and fees


    """

    def __init__(self, adv_participation = .10, adv_period = 21, adv_oi = .05, fee_structure = None):
        self.adv_participation = adv_participation
        self.adv_period = adv_period
        self.adv_oi = adv_oi
        self.fee_structure = STANDARD_FEES if fee_structure is None else fee_structure 
        self.portfolio = None 
        self.manager = None
        self._order_num = 1
        self.order_book = {}
        self.order_log = []
    
    @property
    def order_num(self):
        return self._order_num
        
    def _connect(self, manager, portfolio):
        self.manager = manager
        self.portfolio = portfolio
    
    def _remove_from_ob(self, identifier):
        info = self.order_book[identifier].info
        del self.order_book[identifier]
        self.order_log.append(info)
    
    def _fill_order(self, order, fill_price, filled_units, fees):
        order.fill(self.manager.now, fill_price, filled_units)

        info = order.info
        asset = order.asset
        multiplier = asset.price_stream.multiplier

        self._remove_from_ob(info['identifier'])

        side = info['side']
        cost_basis = side * fill_price * filled_units * multiplier + fees
        fok = info['fok']

        if side == 1:
            self.portfolio.buy(
                    asset,
                    filled_units, 
                    cost_basis
                )
        elif side == -1:
            self.portfolio.sell(
                    asset,
                    filled_units, 
                    cost_basis
                )

        if not fok:
            if filled_units < info['units']:
                self.place_order(
                        side, 
                        asset,
                        info['units'] - filled_units, 
                        time_in_force = info['time_in_force'],
                        order_type = info['order_type'],
                        bands = info['bands']
                    )


    def place_order(self, side, asset, units, time_in_force = None, order_type = 'MARKET', bands = {}, fok = False):
        id_type = asset.id_type
        identifier = asset.identifier

        if identifier in list(self.order_book.keys()):
            self.order_book[identifier].update(self.manager.now)
            self._remove_from_ob(identifier)
        
        self._order_num += 1
        self.order_book[identifier] = Order(
                self.order_num, 
                order_type,
                asset,
                side,
                units,
                self.manager.now, 
                asset.price_stream.close.v,
                bands = bands,
                fok = fok,
            )
    
    def max_shares(self, asset):
        adv = int(asset.price_stream.volume.ts[-self.adv_period:].mean() * self.adv_participation)

        if asset.id_type == 'FUT':
            oi = int(asset.price_stream.open_interest.v * self.adv_oi)
            adv = max(oi, adv)

        return adv


    def process(self):

        for identifier, order in list(self.order_book.items()):
            order.bump()
            info = order.info
            asset = order.asset

            if not asset.tradeable:
                order.cancel(self.manager.now)
                self._remove_from_ob(identifier)
                continue

            side = info['side']
            bands = info['bands']
            order_type = info['order_type']
            units = info['units']
            id_type = info['id_type']
            fee = self.fee_structure[id_type]

            open = asset.price_stream.open.v
            high = asset.price_stream.high.v
            low = asset.price_stream.low.v
            close = asset.price_stream.close.v

            market_value = asset.price_stream.market_value
            multiplier = asset.price_stream.multiplier

            max_shares = self.max_shares(asset)

            filled_units = min(units, max(max_shares, 2))
            order_fill = False

            if order_type == 'MARKET':
                # Market order, drill the close
                order_fill = True
                fill_price = close
            elif order_type == 'LIMIT':
                # regular limit order, fill at lim px
                limit = bands['LIMIT']
                if side == 1:
                    if low <= limit:
                        order_fill = True
                        fill_price = limit
                    elif close <= limit:
                        order_fill = True
                        fill_price = limit
                elif side == -1:
                    if high >= limit:
                        order_fill = True
                        fill_price = limit
                    elif close >= limit:
                        order_fill = True
                        fill_price == limit
            elif order_type == 'LOF':
                # if limit is not hit, drill the close
                limit = bands['LIMIT']
                if side == 1:
                    if low <= limit:
                        order_fill = True
                        fill_price = limit
                    elif close <= limit:
                        order_fill = True
                        fill_price = limit
                    else:
                        order_fill = True
                        fill_price = close

                elif side == -1:
                    if high >= limit:
                        order_fill = True
                        fill_price = limit
                    elif close >= limit:
                        order_fill = True
                        fill_price = limit
                    else:
                        order_fill = True
                        fill_price = close
            elif order_type == 'VWAP':
                # trade the avg of the high and low (maybe add in a vwap field in future)
                order_fill = True
                fill_price = (high + low) / 2
            elif order_type == 'BEST_FILL':
                order_fill = True
                if side == 1:
                    fill_price = low
                elif side == -1:
                    fill_price = high
            elif order_type == 'WORST_FILL':
                order_fill = True
                if side == 1:
                    fill_price = high 
                elif side == -1:
                    fill_price = low 
            elif order_type == 'TRIANGULAR':
                order_fill = True
                fill_price = (high + low + close) / 3
            elif order_type == 'OPEN':
                order_fill = True
                fill_price = open

            if order_fill:
                self._fill_order(order, fill_price, filled_units, fee * filled_units)

            if not order_fill:
                if not info['time_in_force'] is None and info['time_in_force'] >= info['days_on']:
                    order.cancel()
                    self._remove_from_ob(identifier)
