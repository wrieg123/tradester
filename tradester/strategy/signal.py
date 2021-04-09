from numba import jit
import numpy as np




class Signal():

    def __init__(self, indicator, identifiers : tuple, grouping = None, name = None):
        self.indicator = indicator
        self.indicator_name = self.indicator.__class__.__name__ if name is None else name
        self.identifiers = identifiers
        self.grouping = grouping

    def refresh(self):
        self.indicator.refresh()


class SignalGroup():

    def __init__(self):
        self.group = {}
        self.tuple_map = {}
        self.asset_map = {}
        self.inactive_tree = {}
        self.inactive_indicators = {}

    def _get_signals(self, assets):
        #create a cache component for older indicators
        new = []
        for a in assets:
            if self.tuple_map.get(a) is not None:
                for item in self.tuple_map[a]:
                    new.append(item)

        return list(set(new))
        
    def get_indicators(self, assets = None):
        temp_dict = {}
        for k in self._get_signals(assets):
            for s in self.group[k]:
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
                    
        return {k : np.column_stack(tuple(v)) for k, v in list(temp_dict.items())}

   
    def get_indicator_tree(self, assets = None):
        temp_dict = {}
        asset_map_keys = list(self.asset_map.keys())
        for a in assets:
            if a in asset_map_keys:
                for s in self.asset_map[a]:
                    c = a
                    g = s.grouping if s.grouping is not None else 'None'
                    name = s.indicator_name
                    ts = s.indicator.ts

                    #for c in s.identifiers:
                    if c not in list(temp_dict.keys()):
                        temp_dict[c] = {}
                    if g not in list(temp_dict[c].keys()):
                        temp_dict[c][g] = {}

                    if isinstance(ts, list):
                        temp_dict[c][g][name] = np.column_stack(tuple(ts))
                    elif isinstance(ts, dict):
                        temp_dict[c][g][name] = np.column_stack(tuple(ts.values()))
                    else:
                        temp_dict[c][g][name] = np.column_stack([ts])

        return temp_dict

    def _add(self, signal : Signal):
        if not signal.identifiers in self.group.keys():
            self.group[signal.identifiers] = []
        self.group[signal.identifiers].append(signal)

        for identifier in signal.identifiers:
            if identifier not in self.tuple_map.keys():
                self.tuple_map[identifier] = [signal.identifiers]
            else:
                if signal.identifiers not in self.tuple_map[identifier]:
                    self.tuple_map[identifier].append(signal.identifiers)
            if identifier not in self.asset_map.keys():
                self.asset_map[identifier] = [self.group[signal.identifiers][len(self.group[signal.identifiers])-1]]
            else:
                self.asset_map[identifier].append(self.group[signal.identifiers][len(self.group[signal.identifiers]) - 1])
    
    def set_inactive(self, assets):
        new_assets = [a for a in assets if a not in self.inactive_tree.keys()]
        indicator_tree = {}
        for a in new_assets:
            if a in self.asset_map.keys():
                for s in self.asset_map[a]:
                    g = s.grouping if s.grouping is not None else 'None'
                    name = s.indicator_name
                    ts = s.indicator.ts

                    if a not in list(indicator_tree.keys()):
                        indicator_tree[a] = {}
                    if g not in list(indicator_tree[a].keys()):
                        indicator_tree[a][g] = {}

                    if isinstance(ts, list):
                        indicator_tree[a][g][name] = np.column_stack(ts)
                    elif isinstance(ts, dict):
                        indicator_tree[a][g][name] = np.column_stack(ts.values())
                    else:
                        indicator_tree[a][g][name] = np.column_stack([ts])

        tuples = self._get_signals(new_assets)

        self.inactive_tree.update(indicator_tree)

        for a in new_assets:
            if a in self.asset_map.keys():
                del self.asset_map[a]
                del self.tuple_map[a]
        for t in tuples:
            if t in self.group.keys():
                del self.group[t]

    def refresh(self, assets = None):
        for k in self._get_signals(assets):
            for i in self.group[k]:
                i.refresh()
