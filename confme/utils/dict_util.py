from collections import defaultdict
from typing import Any, List, MutableMapping, Dict


def flatten(d: Dict, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep))
        else:
            items.append(new_key)
    return items


class InfiniteDict(defaultdict):
    def __init__(self):
        defaultdict.__init__(self, self.__class__)

    def expand(self, levels: List[str], value: Any):
        if len(levels) <= 0:
            return value

        return self.expand(self[levels[0]], levels[1:], value)
