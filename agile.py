#!/usr/bin/env python3

"""agile, an Android Graphical Interface LExer.

Usage:
  agile.py [-v | -l LOGFILE] LAYOUTS [VALUES]
  agile.py (-h | --help | help)
  agile.py --version

Arguments:
  LAYOUTS     Path to res/layouts.
  VALUES      Path to res/values.

Options:
  -l LOGFILE  Log output to a file.
  -v          Increase verbosity.
  -h --help   Show this screen.
  --version   Display version.

agile is written by Quint Guvernator and licensed by the GPLv3.
"""

VERSION = "0.1.0"

import sys
from bs4 import BeautifulSoup as bs
from docopt import docopt
import pathlib

class Layout:
    def __init__(self, parent, height, width, orientation, gravity=None, subGravity=None):
        self.height = self.inheritable(height, parent, lambda x: x.height)
        self.width = self.inheritable(width, parent, lambda x: x.width)
        self.orientation = orientation

    @staticmethod
    def inheritable(value, parent, getFn):
        if value in ("match_parent", "fill_parent"):
            return getFn(parent)
        else:
            return value

class Clickable:
    def __init__(self, id, parent, height, width, text="", gravity=None):
        self.id = id
        self.parent = parent
        self.height = height
        self.width = width
        self.text = text
        self.gravity = gravity

    @staticmethod
    def resource(value, resourcesPath)
        if not value.startswith("@+"):
            return value

        value.replace("@+", '', 1)
        filename, key = tuple(value.split('/', 1))
        with open(resourcesPath / (filename + ".xml")) as f:
            rsoup = bs(f).find("resources")

        toReturn = rsoup.find(name=key).string
        if toReturn is None:
            raise NameError("Key not found in resources!")

        return toReturn

    @classmethod
    def fromSoup(cls, parent, csoup, resourcesPath):
        text = self.resource(soup["android:text"])
        gravity = self.resource(soup["android:gravity"])

        new = cls(id, parent, height, width, text, gravity)
        return new

if __name__ == "__main__":
    args = docopt(__doc__, version=VERSION)
    layoutPath = args["RES_LAYOUT_PATH"]
