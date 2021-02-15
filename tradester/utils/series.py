from numba import jit, vectorize, float32, int32
import numpy as np


def chunk_up(l , n):
   for i in range(0, len(l), n):
        yield l[i:i+n] 

@jit(nopython = True, nogil = True)
def vectorized_ema(data, window):
    alpha = 2/(window+1)
    alpha_rev = 1-alpha
    n = data.shape[0]
    pows = alpha_rev**(np.arange(n+1))

    scale_arr = 1/pows[:-1]
    offset = data[0]*pows[1:]
    pw0 = alpha*alpha_rev**(n-1)

    mult = data*pw0*scale_arr
    cumsums = mult.cumsum()
    out = offset + cumsums*scale_arr[::-1]

    return out

@jit(nopython = True, nogil = True)
def get_sum(s, p):
    return s[-p:].sum()

@jit(nopython = True, nogil = True)
def get_mean(s, p):
    return s[-p:].mean()

@jit(nopython = True, nogil = True)
def get_std(s, p):
    return s[-p:].std()

@jit(nopython = True, nogil = True)
def get_min(s, p):
    return s[-p:].min()

@jit(nopython = True, nogil = True)
def get_max(s, p):
    return s[-p:].max()

