from .stream import Stream


import numpy as np


class Indicator():
    """
    An Indicator is the transformation of some input data into a signal that can be used for trading.
    
    ...

    Parameters
    ----------
    data : Stream, Dictionary, list
        an individual Stream, a dictionary of Streams or a list of Streams to turn into an indicator
    cache : Integer or None
        amount of data to keep in Streams created
    attributes : list, optional
        list of attributes that an indicator has
    signal_attributes : list, optional
        list of attributes that a signal has
    
    Attributes
    ----------
    pointer : Integer
        current amount of data stored by indicator, used for aligning amount of data in store against indicator
    v : Integer, Dictionary
        the current value of the indicator, if len(attributes) > 1, returns dictionary of values
    ts : np.Array, Dictionary
        np.Array of indicator values, if len(attributes) > 1, return dictionary of np.Array
    signal : Integer, Dictionary  
        the current value of the signal, if len(attributes) > 1, returns dictionary of values
    signals : np.Array, Dictionary 
        np.Array of signal values, if len(attributes) > 1, return dictionary of np.Array
    differential : Integer
        value of difference between indicator pointer and data pointer
    
    Methods
    -------
    __check_data_type(data)
        checks the input data to ensure it is [Stream, list, dictionary] type
    _replay()
        yields chunks of data to replay in the event that the self.differential becomes disjoint
    refresh() 
        refreshes data through the self.calculate user defined method
    calculate(data)
        user defined method for performing calculation of indicator, returns appropriate type as defined by
        the number of attributes (value if 1 attribute, dictionary of values if multiple attributes)
    make_signal()
        user defined method for performing calculation of signal, returns appropriate type as defined by
        the number of attributes (value if 1 attribute, dictionary of values if multiple attributes)

    See Also
    --------
    tradester.feeds.active.Stream
    """

    def __init__(self, data, cache, attributes = ['_indicator']):
        self.data = self.__check_data_type(data)
        self.attributes = attributes
        self._pointer = 0
        for i in attributes:
            setattr(self, i, Stream(cache))
    
    @property
    def pointer(self):
        return self._pointer

    @property
    def v(self):
        #self.refresh()
        if len(self.attributes) == 1:
            return getattr(self, self.attributes[0]).v
        else:
            return {a: getattr(self, a).v for a in self.attributes}

    @property
    def ts(self):
        #self.refresh()
        if len(self.attributes) == 1:
            return getattr(self, self.attributes[0]).ts
        else:
            return {a: getattr(self, a).ts for a in self.attributes}


    @property
    def differential(self):
        if isinstance(self.data, Stream):
            #return self.data.pointer - getattr(self, self.attributes[0]).pointer 
            return self.data.pointer - self.pointer
        elif isinstance(self.data, list):
            return min([d.pointer for d in self.data]) - self.pointer
        elif isinstance(self.data, dict):
            return min([d.pointer for k, d in list(self.data.items())]) - self.pointer
    

    def __check_data_type(self, data):
        if isinstance(data, (Stream, list, dict)):
            return data
        else:
            raise ValueError("Indicator data must be of type: <Stream>, <list>, or <dict>")


    def _replay(self):
        differ = self.differential
        if isinstance(self.data, Stream):
            if differ > 0: 
                for i in range(1, differ):
                    yield self.data.ts[:-i]
                yield self.data.ts
        elif isinstance(self.data, list):
            if differ > 0:
                for i in range(1, differ):
                    yield [d.ts[:-i] for d in self.data]
                yield [d.ts for d in self.data]
        elif isinstance(self.data, dict):
            if differ > 0:
                for i in range(1, differ):
                    yield {k:d.ts[:-i] for k, d in list(self.data.items())}
                yield {k:d.ts for k, d in list(self.data.items())}

    def refresh(self):
        for ds in self._replay():
            if len(self.attributes) == 1:
                getattr(self, self.attributes[0]).push(self.calculate(ds))
            else:
                for a, v in list(self.calculate(ds).items()):
                    getattr(self, a).push(v)
            self._pointer += 1
    

    def calculate(self, data):
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
