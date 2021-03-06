from .order import Order

import numpy as np

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
   

    Attributes
    ----------
    portfolio : tradester.portfolios.Portfolio
        the connected portfolio object
    manager : tradester.factories.ClockManager
        the connected central clock
    order_num : int
        the current order number (for tracking in the logs)
    order_book : dict
        a one sided order book (i.e. each contract can only have one entry)
    order_log : list
        a log of all orders and order actions during the runtime
    
    Methods
    -------
    _connect(manager : tradester.factories.ClockManager, portfolio : tradester.portfolios.Portfolio)
        used in the engine to connect the oms to the central ClockManager and Portfolio
    _remove_from_ob(identifier : string)
        removes the identifier order from the order_book, appends the order info to the order_log
    _fill_order(order : tradester.oms.Order, fill_price : float, filled_units : int, fees : float)
        fills the order, places the trade into the portfolio
    place_order(side : int, asset : tradester.finance.Asset, units : int, time_in_force : int, optional, order_type : string, bands : dict, fok : bool, optional)
        places the order onto the order_book with the desired paramaters: side = 1 is buy, side = -1 is sell
        - possible order_types:
            MARKET -> fills at close
            OPEN -> fills at open
            LIMIT -> fills at limit price, limit prices defined in bands kwarg (ex: bands = {'LIMIT': 100}), order remains open till filled or updated
            RANGE -> fills at avg of high and low price
            RANGE_BOUND_C -> fills at the average of the low and close for a buy or high and close for a sell
            RANGE_BOUND_O -> fills at the average of the low and open for a buy or high and open for a sell
            INVERSE_BOUND_C -> fills at the average of the low and close for a sell or high and close for a buy 
            INVERSE_BOUND_O -> fills at the average of the low and open for a sell or high and open for a buy 
            BEST_FILL -> fills at the low for a buy and high for a sell
            WORST_FILL -> fills at the low for a sell and high for a buy 
            TRIANGULAR_C -> fills at the average of high, low, and close
            TRIANGULAR_O -> fills at the average of high, low, and open
            BAR_AVG -> fills at the average of open, high, low, and close   
    max_shares(asset : tradester.finance.Asset)
        returns the maximum tradeable shares based on adv_participation and adv_oi if applicable
    process()
        processes all orders on the order_book to check for fills
         
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
        if identifier in self.order_book.keys():
            info = self.order_book[identifier].info
            del self.order_book[identifier]
            self.order_log.append(info)

    def _log_order(self, order):
        self.order_log.append(order.info)
    
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


    def place_order(self, side, asset, units, time_in_force = None, order_type = 'MARKET', bands = {}, fok = False, peg_to_open = False, temp = False):
        id_type = asset.id_type
        identifier = asset.identifier

        if identifier in list(self.order_book.keys()):
            self.order_book[identifier].update(self.manager.now)
            self._remove_from_ob(identifier)
        
        self._order_num += 1
        if temp:
            return Order(
                self.order_num, 
                order_type,
                asset,
                side,
                units,
                self.manager.now, 
                asset.price_stream.close.v,
                bands = bands,
                fok = fok,
                peg_to_open = peg_to_open,
            )
        else:
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
                    peg_to_open = peg_to_open,
                )
    
    def max_shares(self, asset):
        adv = int(asset.price_stream.volume.ts[-self.adv_period:].mean() * self.adv_participation)

        if asset.id_type == 'FUT':
            oi = int(asset.price_stream.open_interest.v * self.adv_oi)
            adv = max(oi, adv)

        return adv


    def _process_single_order(self, identifier, order):
        order.bump()
        info = order.info
        asset = order.asset

        if not asset.tradeable:
            order.cancel(self.manager.now)
            self._remove_from_ob(identifier)
            return

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
            order_fill = True
            fill_price = close
        elif order_type == 'OPEN':
            order_fill = True
            fill_price = open
        elif order_type == 'LIMIT':
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
        elif order_type == 'RANGE':
            order_fill = True
            fill_price = (high + low) / 2
        elif order_type == 'RANGE_BOUND_C':
            order_fill = True
            if side == 1:
                fill_price = (low + close) / 2
            elif side == -1:
                fill_price = (high + close) / 2
        elif order_type == 'INVERSE_BOUND_C':
            order_fill = True
            if side == 1:
                fill_price = (high + close) / 2
            elif side == -1:
                fill_price = (low + close) / 2
        elif order_type == 'RANGE_BOUND_O':
            order_fill = True
            if side == 1:
                fill_price = (low + open) / 2
            elif side == -1:
                fill_price = (high + open) / 2
        elif order_type == 'INVERSE_BOUND_O':
            order_fill = True
            if side == 1:
                fill_price = (high + open) / 2
            elif side == -1:
                fill_price = (low + open) / 2
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
        elif order_type == 'TRIANGULAR_C':
            order_fill = True
            fill_price = (high + low + close) / 3
        elif order_type == 'TRIANGULAR_O':
            order_fill = True
            fill_price = (high + low + open) / 3
        elif order_type == 'BAR_AVG':
            order_fill = True
            fill_price = (high + low + open + close) / 4
        elif order_type == 'TWAP':
            order_fill = True
            if close > open:
                ol = (open + low) / 2
                hl = (high + low) / 2
                hc = (high + close) / 2
                fill_price = (ol + hl + hc) / 3
            else:
                oh = (open + high) / 2
                hl = (high + low) / 2
                lc = (low + close) / 2
                fill_price = (oh+hl+lc)/3

        if order_fill:
            self._fill_order(order, fill_price, filled_units, fee * filled_units)

        if not order_fill and not order.canceled:
            if not info['time_in_force'] is None and info['time_in_force'] >= info['days_on']:
                order.cancel()
                self._remove_from_ob(identifier)

    def _process_complex_order(self, identifier, order):
        order.bump()
        info = order.info
        asset = order.asset

        if not asset.tradeable:
            order.cancel(self.manager.now)
            self._remove_from_ob(identifier)
            return 

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

        order.working()
        self._remove_from_ob(identifier)

        bid = bands['BID']
        ask = bands['ASK']
        if order.peg_to_open:
            bid = open - bid
            ask = open + ask
        bid_order = self.place_order(1, asset, units, temp = True)
        ask_order = self.place_order(-1, asset, units, order_type = 'MM', temp = True)

        if isinstance(bid, str) and isinstance(ask, str):
            if bid == 'BEST':
                self._fill_order(bid_order, low, filled_units, fee * filled_units)
            if ask == 'BEST':    
                self._fill_order(ask_order, high, filled_units, fee * filled_units)
            if bid == 'OPEN':
                self._fill_order(bid_order, open, filled_units, fee * filled_units)
            if bid == 'CLOSE':
                self._fill_order(bid_order, close, filled_units, fee * filled_units)
            if ask == 'OPEN':
                self._fill_order(ask_order, open, filled_units, fee * filled_units)
            if ask == 'CLOSE':
                self._fill_order(ask_order, close, filled_units, fee * filled_units)
            self._log_order(bid_order)
            self._log_order(ask_order)

        else:
            take_trade = False
            if low <= bid or high >= ask:
                take_trade = True
            if take_trade:
                if low < bid:
                    self._fill_order(bid_order, bid, filled_units, fee * filled_units)
                else:
                    self._fill_order(bid_order, close, filled_units, fee * filled_units)
                
                if high > ask:
                    self._fill_order(ask_order, ask, filled_units, fee * filled_units)
                else:
                    self._fill_order(ask_order, close, filled_units, fee * filled_units)

                self._log_order(bid_order)
                self._log_order(ask_order)



    def process(self):

        for identifier, order in list(self.order_book.items()):
            if order.side != 0:
                self._process_single_order(identifier, order)
            else:
                self._process_complex_order(identifier, order)
