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


def resource(value, resourcesPath)
    if not value.startswith("@+"):
        return value

    value.replace("@+", '', 1)
    filename, key = tuple(value.split('/', 1))
    with open(resourcesPath / (filename + ".xml")) as f:
        rsoup = bs(f).find("resources")

    toReturn = rsoup.find(name=key).string

    return toReturn


def inheritable(value, parent, getFn):
    if value in ("match_parent", "fill_parent"):
        return getFn(parent)
    else:
        return value


class Layout:

    def __init__(self, parent, height, width, orientation, gravity=None, subGravity=None, children):
        self.height = inheritable(height, parent, lambda x: x.height)
        self.width = inheritable(width, parent, lambda x: x.width)
        self.orientation = orientation
        self.children = children

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        id = soup["android:id"]
        height = soup["android:layout_height"]
        width = soup["android:layout_width"]
        # TODO

        new = cls(id, parent, height, width, orientation, gravity, subGravity, children)
        return new


class Clickable:

    def __init__(self, id, parent, height, width, text="", gravity=None):
        self.id = id
        self.parent = parent
        self.height = inheritable(height, parent, lambda x: x.height)
        self.width = inheritable(height, parent, lambda x: x.height)
        self.text = text
        self.gravity = gravity

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        id = soup["android:id"]
        height = soup["android:layout_height"]
        width = soup["android:layout_height"]
        text = self.resource(soup["android:text"], resourcesPath)
        gravity = soup["android:gravity"]

        new = cls(id, parent, height, width, text, gravity)
        return new

if __name__ == "__main__":
    args = docopt(__doc__, version=VERSION)
    layoutPath = args["RES_LAYOUT_PATH"]
