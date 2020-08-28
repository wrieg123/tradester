import numpy as np

class Signal():



    def __init__(self, indicator, identifiers, grouping = None):
        self.indicator = indicator
        self.indicator_name = self.indicator.__class__.__name__
        self.identifiers = identifiers if isinstance(identifiers, list) else [identifiers]
        self.grouping = grouping
   


    def refresh(self):
        self.indicator.refresh()



class SignalGroup():



    def __init__(self):
        self.group = []
  


    @property
    def vector_space(self):
        temp_dict = {}
        for s in self.group:
            for c in s.identifiers:
                ts = s.indicator.ts
                if c in list(temp_dict.keys()):
                    if isinstance(ts, list):
                        for t in ts:
                            temp_dict[c].append(t)
                    elif isinstance(ts, dict):
                        for t in list(ts.values()):
                            temp_dict[c].append(t)
                    else:
                        temp_dict[c].append(ts)
                else:
                    if isinstance(ts, list):
                        temp_dict[c] = [t for t in ts]
                    elif isinstance(ts, dict):
                        temp_dict[c] = [t for t in list(ts.values())]
                    else:
                        temp_dict[c] = [ts]
                    
        return {k : np.column_stack(v) for k, v in list(temp_dict.items())}
   
    @property
    def full_vector_space(self):
        temp_dict = {}
        for s in self.group:
            g = s.grouping
            name = s.indicator_name
            ts = s.indicator.ts
            for c in s.identifiers:
                if not c in temp_dict.keys():
                    temp_dict[c] = {}
                if not g in temp_dict[c].keys():
                    temp_dict[c][g] = {}
                if isinstance(ts, list):
                    temp_dict[c][g][name] = np.column_stack([t for t in ts])
                elif isinstance(ts, dict):
                    temp_dict[c][g][name] = np.column_stack([t for t in list(ts.values())])
                else:
                    temp_dict[c][name] = np.column_stack([ts])

        return temp_dict


    def _add(self, signal : Signal):
        self.group.append(signal)


    def refresh(self):
        for i in self.group:
            i.refresh()
