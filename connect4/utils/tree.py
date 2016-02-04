__author__ = 'reut'

import logging
import os
LOGGER = logging.getLogger("Tree")
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
LOGGER.addHandler(sh)
LOGGER.setLevel(logging.INFO)


# absorb and replace last state? open-listing of states... (just guessing)
class Tree(object):

    def __init__(self, data, parent=None):
        self.leaves = parent.leaves if parent else [self]
        self.parent = parent
        self.depth = parent.depth + 1 if parent else 0
        self.data = data
        self.children = []

    def add_child(self, data):
        try:
            self.leaves.remove(self)
        except ValueError:
            LOGGER.debug("%s Not in tree..." % self)
        child = Tree(data=data, parent=self)
        self.children.append(child)
        self.leaves.append(child)

    def __str__(self):
        return os.linesep.join(["Tree:", "data:", "%s", "children:", "%s"]) % (self.data, self.children)

    def __repr__(self):
        return self.__str__()