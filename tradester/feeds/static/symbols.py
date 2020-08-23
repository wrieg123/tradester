from .feed import MetaFeed, CustomFeed, TSFeed 

import pandas as pd

__all__ = ['SymbolsMeta', 'SymbolsTS', 'SearchSymbols']


class SymbolsMeta(MetaFeed):

    def __init__(self, identifiers, credentials = None):
        super().__init__(identifiers, "*", "symbols", "symbol", credentials)


class SearchSymbols(CustomFeed):
    
    def __init__(self, search_str, credentials = None, try_tmp = True):
        super().__init__("", try_tmp, credentials, override = True)
        self.search_str = search_str
        self._data = self.__gather_data()    

    def __gather_data(self):
        query = "select * from symbols where name like '%{}%'".format(self.search_str)
        df = self._query(query)

        if not df.empty:
            symbols = list(df['symbol'])
            print(f"Found {len(symbols)} matching symbols ...", '\n')
            metas = SymbolsMeta(symbols, credentials = self.credentials).data
            for symbol, info in metas.items():
                print(symbol, '->', info, '\n')
            return metas
        else:
            print(f"No symbol names matched '{self.search_str}'.")
            return {}


class SymbolsTS(TSFeed):
    
    def __init__(self, identifiers, date_fields = "date_released, date_effective", start_date = None, end_date = None, date_filter = "date_effective", credentials = None, filter_revisions = None):
        super().__init__(identifiers, "value, is_revision", "symbols", "symbol", credentials, None, start_date, end_date, override = True)
        self.date_fields = date_fields
        self.date_filter = date_filter 
        self.filter_revisions = filter_revisions
        self._data = self.__gather_data()

    def __gather_data(self):
        if self.identifiers_type is list:
            query = "select {}, symbol, {} from {} where symbol in ({})".format(self.date_fields, self.fields, self.database, str(self.identifiers).strip('[]'))
        else:
            query = "select {}, symbol, {} from {} where symbol = '{}'".format(self.date_fields, self.fields, self.database, self.identifiers)
        
        if self.filter_revisions is not None:
            _filter = str(self.filter_revisions).lower()
            query += " and is_revision = {}".format(_filter)
        
        if self.start_date:
            query += " and {} >= '{}'".format(self.date_filter, self.start_date)
        if self.end_date:
            query += " and {} <= '{}'".format(self.date_filter, self.end_date)
        df = self._query(query)
        df[self.date_filter] = pd.to_datetime(df[self.date_filter], format='%Y-%m-%d')
        df = df.pivot_table(index = self.date_fields.split(', '), columns = 'symbol', values = 'value')
        return df
