#
# Dictionaries with additional behaviour.
#

import collections


class LeastRecentlyUsedDict(collections.OrderedDict):
    """A dict with a maximum size, evicting the least recently written key when full.

    Getting a key that is not present returns a default value of 0.

    Setting a key marks it as most recently used and removes the oldest key if full.

    May be useful for tracking the count of items where limited memory usage is needed even if
    the set of items can be unlimited.

    Based on the example at
    https://docs.python.org/3/library/collections.html#ordereddict-examples-and-recipes
    """

    def __init__(self, maxsize=128, *args, **kwargs):
        self.maxsize = maxsize
        super().__init__(*args, **kwargs)

    def __getitem__(self, key):
        if key in self:
            return super().__getitem__(key)
        return 0

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if self.maxsize < len(self):
            self.popitem(last=False)
