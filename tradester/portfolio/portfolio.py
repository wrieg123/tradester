from .position import Position

import pandas as pd


class Portfolio():

    def __init__(self, starting_cash, print_trades = False):
        self._cash = starting_cash
        self._value = starting_cash
        self.print_trades = print_trades
        self._long_equity = 0
        self._short_equity = 0
        self._pnl = 0
        self.manager = None
        self.universes = None
        self._positions = {}
        self.values = []
        self.holdings = []
        self.trading_log = []
    
    @property
    def cash(self):
        return self._cash
    
    @property
    def pnl(self):
        return self._pnl

    @property
    def value(self):
        return self._value
    
    @property
    def long_equity(self):
        return self._long_equity
    
    @property
    def short_equity(self):
        return self._short_equity

    @property
    def positions(self):
        return {i: v.info for i, v in list(self._positions.items())}

    @property
    def info(self):
        return {
            'date': self.manager.now,
            'value': self.value,
            'cash': self.cash,
            'long_equity': self.long_equity,
            'short_equity': self.short_equity,
            'pnl': self.pnl,
        }
    
    @property
    def holdings_df(self):
        return pd.DataFrame(self.holdings)

    @property
    def values_df(self):
        return pd.DataFrame(self.values)
    
    @property
    def trading_log_df(self):
        return pd.DataFrame(self.trading_log)

    def _connect(self, manager, universes):
        self.manager = manager
        self.universes = universes
    
    def log_trade(self, log):
        self.trading_log.append(log)

    def buy(self, asset, units, cost_basis):
        id_type = asset.id_type
        identifier = asset.identifier

        if self.print_trades:
            print(self.manager.now, 'BOT', id_type, identifier, round(units), round(cost_basis))
        
        self._cash -= cost_basis

        if not identifier in self.positions.keys():
            self._positions[identifier] = Position(
                                            asset,
                                            1,
                                            units,
                                            cost_basis
                                        )
        else:
            current = self._positions.pop(identifier).info
            pos_delta = (current['side']*current['units']) + units
            cb_delta = current['cost_basis'] + cost_basis
            
            if current['side'] == -1:
                trade = {
                    'date': self.manager.now,
                    'id_type': id_type,
                    'identifier': identifier,
                    'side': 1,
                    'gross': cb_delta,
                    'per contract': cb_delta / units,
                }
                self.log_trade(trade)


            if pos_delta != 0:
                side = 1 if pos_delta > 0 else -1
                self._positions[identifier] = Position(
                                                asset,
                                                side,
                                                abs(pos_delta),
                                                cb_delta
                                            )
    
    def sell(self, asset, units, cost_basis):
        id_type = asset.id_type
        identifier = asset.identifier

        if self.print_trades:
            print(self.manager.now, 'SLD', id_type, identifier, round(units), round(cost_basis))
        
        self._cash -= cost_basis

        if not identifier in self.positions.keys():
            self._positions[identifier] = Position(
                                            asset,
                                            -1,
                                            units,
                                            cost_basis,
                                        )

        else:
            current = self._positions.pop(identifier).info
            pos_delta = (current['side']*current['units']) - units 
            cb_delta = current['cost_basis'] + cost_basis
            
            if current['side'] == 1:
                trade = {
                    'date': self.manager.now,
                    'id_type': id_type,
                    'identifier': identifier,
                    'side': 1,
                    'gross': cb_delta,
                    'per contract': cb_delta / units,
                }
                self.log_trade(trade)

            if pos_delta != 0:
                side = 1 if pos_delta > 0 else -1
                self._positions[identifier] = Position(
                                                asset,
                                                side,
                                                abs(pos_delta),
                                                cb_delta
                                            )
    
    def reconcile(self):
        """Reconciles portfolio value at end of trading day"""
        market_value = 0
        long_equity = 0
        short_equity = 0
        pnl = 0

        for identifier, position in self_positions.items():
            asset = position.asset

            info = position.info
            info['date'] = self.manager.now
            self.holdings.append(info)

            pnl += position['pnl']

            if not asset.tradeable:
                if self.print_trades:
                    print('SETTLE', identifier, round(position['market_value']))
                del self._positions[identifier]
                self._cash += position['market_value']
            else:
                if info['side'] == 1:
                    long_equity += position['market_value']
                else:
                    short_equity += position['market_value']

        self._long_equity = long_equity
        self._short_equity = short_equity
        self._pnl = pnl
        self._value = self.long_equity + self.short_equity + self.cash

        self.values.append(self.info)
