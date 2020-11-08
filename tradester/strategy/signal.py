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

    def _get_signals(self, assets):
        if assets is None:
            return list(self.group.keys())
        keys = []
        for asset in assets:
            for k in list(self.group.keys()):
                if asset in k:
                    keys.append(k)
        keys = list(set(keys))
        return keys

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
                    
        return {k : np.column_stack(v) for k, v in list(temp_dict.items())}

   
    def get_indicator_tree(self, asset = None):
        temp_dict = {}
        for k in self._get_signals(assets):
            for s in self.group[k]:
                g = s.grouping if s.grouping is not None else 'None'
                name = s.indicator_name
                ts = s.indicator.ts

                for c in s.identifiers:
                    if c not in temp_dict.keys():
                        temp_dict[c] = {}
                    if g not in temp_dict[c].keys():
                        temp_dict[c][g] = {}

                    if isinstance(ts, list):
                        temp_dict[c][g][name] = np.column_stack([t for t in ts])
                    elif isinstance(ts, dict):
                        temp_dict[c][g][name] = np.column_stack([t for t in list(ts.values())])
                    else:
                        temp_dict[c][g][name] = np.column_stack([ts])

        return temp_dict


    def _add(self, signal : Signal):
        if not signal.identifiers in self.group.keys():
            self.group[signal.identifiers] = []
        self.group[signal.identifiers].append(signal)


    def refresh(self, assets = None):
        for k in self._get_signals(assets):
            for i in self.group[k]:
                i.refresh()
