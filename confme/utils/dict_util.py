import collections.abc
from collections import defaultdict
from typing import Any, List, MutableMapping, Dict, Tuple


def flatten(d: Dict, parent_key='', sep='.') -> Tuple[List, List]:
    items = []
    values = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            inner_items, inner_values = flatten(v, new_key, sep=sep)
            items.extend(inner_items)
            values.extend(inner_values)
        else:
            items.append(new_key)
            values.append(v)
    return items, values


def recursive_update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = recursive_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


class InfiniteDict(defaultdict):
    def __init__(self):
        defaultdict.__init__(self, self.__class__)

    def expand(self, levels: List[str], value: Any):
        current = self
        for level in levels[:-1]:
            current = current[level]

        current[levels[-1]] = value
