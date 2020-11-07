from tradester.finance.assets import Future, Security
from .stream import Stream


class Indicator():
    
    def __init__(self, data, attributes = ['_indicator']):
        self.data = data
        self.attributes = attributes
        self._pointer = 0
        for i in attributes:
            setattr(self, i, Stream(None))
    
    @property
    def pointer(self):
        return self._pointer
    
    @property
    def v(self):
        if len(self.attributes) == 1:
            return getattr(self, self.attributes[0]).v
        else:
            return {a: getattr(self, a).v for a in self.attributes}

    @property
    def ts(self):
        if len(self.attributes) == 1:
            return getattr(self, self.attributes[0]).ts
        else:
            return {a: getattr(self, a).ts for a in self.attributes}
    
    def refresh(self):
        should_refresh = True

        if isinstance(self.data, (Future, Security)):
            should_refresh = self.data.tradeable

        if should_refresh:
            if len(self.attributes) == 1:
                getattr(self, self.attributes[0]).push(self.calculate())
            else:
                for a, v in list(self.calculate().items()):
                    getattr(self, a).push(v)
            self._pointer += 1
    
    def calculate(self):
        raise NotImplementedError("For each active indicator, you must implement a calculate(self, data) method")


class IndicatorGroup():
    """
    IndicatorGroup helps organize and store indicators by refreshing baskets of them at a time
    
    ...

    Attributes
    ----------
    group : Dictionary
        stores individual indicator by name
    
    Methods
    -------
    add(name : String, indicator : Indicator)
        adds indicator by name to self.group
    refresh_all()
        refreshes all indicators in the group
    refresh(name : String)
        refreshes indicator by name

    See Also
    --------
    etl.feeds.active.Indicator
    """
    def __init__(self, group_type = 'list'):
        if group_type == 'list':
            self.group = []
        elif group_type == 'dict':
            self.group = {}

    def add(self, indicator : Indicator, name = None):
        if isinstance(self.group, list):
            self.group.append(indicator)
        elif isinstance(self.group, dict):
            self.group[name] = indicator
    
    def refresh(self):
        if isinstance(self.group, list):
            for i in self.group:
                i.refresh()
        elif isinstance(self.group, dict):
            for i in list(self.group.values()):
                i.refresh()

