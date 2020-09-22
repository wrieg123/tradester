import numpy as np


def chunk_up(l , n):
   for i in range(0, len(l), n):
        yield l[i:i+n] 


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



def stateful_performance(performance_ts, states, normalize = False, log_normal = False):
    state_performance = {}
    time_in_state = 1

    prev_state = -1
    prev_price = None
    for i in range(len(performance_ts)):
        state = states[i]
        current_price = performance_ts[i]

        if not prev_price is None and state != prev_state and prev_state != -1 and str(prev_state) != 'nan':
            if log_normal:
                performance = np.log(current_price / prev_price)
            else:
                performance = current_price / prev_price - 1

            if normalize:
                performance = performance / time_in_state

            if not prev_state in state_performance.keys():
                state_performance[prev_state] = [performance]
            else:
                state_performance[prev_state].append(performance)
            
            time_in_state = 1
            prev_price = current_price
        else:
            time_in_state += 1

        prev_state = state
            
        if prev_price is None:
            prev_price = current_price
    
    return state_performance




def stateful_log_performance(performance, states, normalize = False):
    prev_state = -1
    state_performance = {}
    perf = None
    time_in_state = 1
    for i in range(len(performance)):
        state = states[i]
        curr = performance[i]

        if perf is None:
            perf = curr
        if state != prev_state and prev_state != -1 and str(prev_state) != 'nan':
            if not prev_state in state_performance.keys():
                if normalize:
                    state_performance[prev_state] = [np.log(curr/perf)/time_in_state]
                else:
                    state_performance[prev_state] = [np.log(curr/perf)]
            else:
                if normalize:
                    state_performance[prev_state].append(np.log(curr/perf)/time_in_state)
                else:
                    state_performance[prev_state].append(np.log(curr/perf))
            perf = curr
            time_in_state = 1
        else:
            time_in_state += 1
        prev_state = state
    return state_performance

