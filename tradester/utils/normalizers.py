from tradester.utils import get_max, get_min, get_std, get_mean
import numpy as np


class Normalizer():

    def __init__(self, roll_period, min_period):
        self.roll_period = roll_period
        self.min_period = min_period


class MeanStdNormalizer(Normalizer):
    
    def __init__(self, roll_period = None, min_period = None):
        super().__init__(roll_period, min_period)

    def normalize(self, x):
        if self.min_period is not None:
            if len(x) < self.min_period:
                return 0
            p = len(x)

        if self.roll_period is not None:
            p = self.roll_period
            x = x[-p:]
            
        mu = get_mean(x, p)
        std = get_std(x, p)

        return (x[-1] - mu) / std

class RankNormalizer(Normalizer):

    def __init__(self, roll_period = None, min_period = None):
        super().__init__(roll_period, min_period)

    def normalize(self, x):
        if self.min_period is not None:
            if len(x) < self.min_period:
                return 0.5
            p = len(x)

        if self.roll_period is not None:
            p = self.roll_period
            x = x[-p:]
            
        mx = get_max(x, p)
        mn = get_min(x, p)

        if np.isclose(mx-mn,0):
            return 0.5
        
        return (x - mn) / (mx - mn)
