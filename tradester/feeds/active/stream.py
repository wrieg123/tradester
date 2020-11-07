import numpy as np
import math


class Stream():
    """
    A stream is the fundamental unit of data storage for active feeds. It allows for ordered inclusion of data
    in a more memory efficient manner.
    
    ...
    
    Parameters
    ----------
    cache : Integer, None
        amount of data to keep in memory
    
    Attributes
    ----------
    ts : np.Array
        np.Array of data stored in time series
    v : Integer, None
        most recent entry in the stream, otherwise None
    len : Integer
        length of the stream data
    pointer : Integer
        maintains the current 'time' within the Stream
        
    Methods
    -------
    ffill()
        fills in most recent value
    push(x)
        pushes datapoint x onto the stream assuming it is none None or 'nan'

    """

    def __init__(self, cache):
        self.cache = cache
        self._stream = []
        #self._stream = np.array([]) 
        self._pointer = 0
    
    @property
    def ts(self):
        #return self._stream
        return np.array(self._stream) 

    @property
    def v(self):
        if len(self._stream) > 0:
           return self._stream[-1]
        else:
            return None

    @property
    def len(self):
        return len(self._stream)

    @property
    def pointer(self):
        return self._pointer
    
    def __add__(self, other):
        if self.pointer == 0 or other.pointer == 0:
            return None
        shift = self.pointer - other.pointer
        if shift > 0:
            return self.ts[abs(shift):] + other.ts
        elif shift < 0:
            return self.ts + other.ts[abs(shift):]
        else:
            return self.ts + other.ts

    def __sub__(self, other):
        shift = self.pointer - other.pointer
        if self.pointer == 0 or other.pointer == 0:
            return None
        if shift > 0:
            return self.ts[abs(shift):] - other.ts
        elif shift < 0:
            return self.ts - other.ts[abs(shift):]
        else:
            return self.ts - other.ts

    def __mul__(self, other):
        shift = self.pointer - other.pointer
        if self.pointer == 0 or other.pointer == 0:
            return None
        if shift > 0:
            return self.ts[abs(shift):] * other.ts
        elif shift < 0:
            return self.ts * other.ts[abs(shift):]
        else:
            return self.ts * other.ts

    def __truediv__(self, other):
        shift = self.pointer - other.pointer
        if self.pointer == 0 or other.pointer == 0:
            return None
        if shift > 0:
            return self.ts[abs(shift):] / other.ts
        elif shift < 0:
            return self.ts / other.ts[abs(shift):]
        else:
            return self.ts / other.ts

    def _check_cache(self):
        if not self.cache is None:
            self._stream = self._stream[-self.cache:]
    

    def push(self, x):
        if str(x) != 'nan' or not x is None:
            self._stream = np.append(self._stream, x)
            #self._stream.append(x)
            self._pointer += 1
            #self._check_cache()
        else:
            raise ValueError('The input type is not in (int, float)')
        

