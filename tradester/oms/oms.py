from .order import Order


STANDARD_FEES = {
    'FUT': 3.00,
    'SEC': 0.01,
}

class OMS():

    def __init__(self, adv_participation = .15, adv_period = 21, adv_oi = .05, fee_structure = None):
        self.adv_participation = adv_participation
        self.adv_period = adv_period
        self.adv_oi = adv_oi
        self.fee_structure = STANDARD_FEES if fee_structure is None else fee_structure 
        self.portfolio = None 
        self.manager = None
        self.universes = None
        self._order_num = 1
        self.order_book = {}
        self.order_log = []
    
    @property
    def order_num(self):
        return self._order_num
        
    def _connect(self, manager, portfolio, universes):
        self.manager = manager
        self.portfolio = portfolio
        self.universes = universes
    
    def _remove_from_ob(self, identifier):
        info = self.order_book[identifier].info
        del self.order_book[identifier]
        self.order_log.append(info)
    
    def _fill_order(self, order, fill_price, filled_units, multiplier, fees):
        order.fill(self.manager.now, fill_price, filled_units)

        info = order.info

        self._remove_from_ob(info['identifier'])
        side = info['side']
        cost_basis = side * fill_price * filled_units * multiplier
        fok = info['fok']

        if side == 1:
            self.portfolio.buy(
                    info['id_type'], 
                    info['identifier'], 
                    filled_units, 
                    cost_basis + fees, 
                    info['universe'],
                    multiplier
                )
        elif side == -1:
            self.portfolio.sell(
                    info['id_type'], 
                    info['identifier'], 
                    filled_units, 
                    cost_basis + fees, 
                    info['universe'],
                    multiplier
                )
        if not fok:
            if filled_units < info['units']:
                self.place_order(
                        side, 
                        info['id_type'], 
                        info['identifier'], 
                        info['units'] - filled_units, 
                        info['universe'], 
                        time_in_force = info['time_in_force'],
                        order_type = info['order_type'],
                        bands = info['bands']
                    )

    def max_shares(self, id_type, identifier, universe):
        if self.universes[universe].streams[identifier].volume.pointer == 0:
            return 0
        else:
            adv = self.universes[universe].streams[identifier].volume.ts[-self.adv_period:].mean()
        
        if id_type == 'FUT':
            oi = self.universes[universe].streams[identifier].open_interest.v
        else:
            oi = None
        
        if not oi is None:
            if adv is None:
                return oi * self.adv_oi
            else:
                return adv
        return adv


    def place_order(self, side, id_type, identifier, units, universe, time_in_force = None, order_type = 'MARKET', bands = {}, fok = False):
        if identifier in list(self.order_book.keys()):
            self.order_book[identifier].update(self.manager.now)
            self._remove_from_ob(identifier)
        
        self._order_num += 1
        self.order_book[identifier] = Order(
                self.order_num, 
                order_type,
                universe,
                id_type,
                identifier,
                side,
                units,
                self.manager.now, 
                self.universes[universe].streams[identifier].close.v,
                bands = bands,
                fok = fok,
            )


    def process(self):

        for identifier, order in list(self.order_book.items()):
            order.bump()
            info = order.info
            universe = info['universe'] 
            inactive = getattr(self.universes[universe], 'inactive', None)

            if not inactive is None:
                if identifier in self.universes[universe].inactive:
                    order.cancel(self.manager.now)
                    self._remove_from_ob(identifier)
                    continue
            
            side = info['side']
            bands = info['bands']
            order_type = info['order_type']
            units = info['units']
            id_type = info['id_type']
            fee = self.fee_structure[id_type]

            open = self.universes[universe].streams[identifier].open.v
            high = self.universes[universe].streams[identifier].high.v
            low = self.universes[universe].streams[identifier].low.v
            close = self.universes[universe].streams[identifier].close.v

            market_value = self.universes[universe].streams[identifier].market_value
            multiplier = self.universes[universe].active_info[identifier]['multiplier'] if id_type == 'FUT' else 1
            try:
                max_shares = int(self.max_shares(id_type, identifier, universe))
            except:
                max_shares = 0

            filled_units = min(units, max(max_shares, 5))
            order_fill = False

            #def _fill_order(self, order, fill_price, filled_units, multiplier, fees):
            if order_type == 'MARKET':
                # Market order, drill the close
                order_fill = True
                self._fill_order(order, close, filled_units, multiplier, fee * filled_units)
            elif order_type == 'LIMIT':
                # regular limit order, fill at lim px
                limit = bands['LIMIT']
                if side == 1:
                    if low <= limit:
                        order_fill = True
                        self._fill_order(order, limit, filled_units, multiplier, fee * filled_units)
                    elif close <= limit:
                        order_fill = True
                        self._fill_order(order, limit, filled_units, multiplier, fee * filled_units)
                elif side == -1:
                    if high >= limit:
                        order_fill = True
                        self._fill_order(order, limit, filled_units, multiplier, fee * filled_units)
                    elif close >= limit:
                        order_fill = True
                        self._fill_order(order, limit, filled_units, multiplier, fee * filled_units)
            elif order_type == 'LOF':
                # if limit is not hit, drill the close
                limit = bands['LIMIT']
                if side == 1:
                    if low <= limit:
                        order_fill = True
                        self._fill_order(order, limit, filled_units, multiplier, fee * filled_units)
                    elif close <= limit:
                        order_fill = True
                        self._fill_order(order, limit, filled_units, multiplier, fee * filled_units)
                    else:
                        order_fill = True
                        self._fill_order(order, close, filled_units, multiplier, fee * filled_units)

                elif side == -1:
                    if high >= limit:
                        order_fill = True
                        self._fill_order(order, limit, filled_units, multiplier, fee * filled_units)
                    elif close >= limit:
                        order_fill = True
                        self._fill_order(order, limit, filled_units, multiplier, fee * filled_units)
                    else:
                        order_fill = True
                        self._fill_order(order, close, filled_units, multiplier, fee * filled_units)
            elif order_type == 'VWAP':
                # trade the avg of the high and low (maybe add in a vwap field in future)
                order_fill = True
                self._fill_order(order, (high + low)/2, filled_units, multiplier, fee * filled_units)


            if not order_fill:
                if not info['time_in_force'] is None and info['time_in_force'] >= info['days_on']:
                    order.cancel()
                    self._remove_from_ob(identifier)
