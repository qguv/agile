#!/usr/bin/env python3

"""agilex, the Android Graphical Interface LEXer

Usage:
  agilex.py [-v | -l LOGFILE] LAYOUTS [VALUES]
  agilex.py (-h | --help | help)
  agilex.py --version

Arguments:
  LAYOUTS     Path to res/layouts.
  VALUES      Path to res/values.

Options:
  -l LOGFILE  Log output to a file.
  -v          Increase verbosity.
  -h --help   Show this screen.
  --version   Display version.

agilex is written by Quint Guvernator and licensed by the GPLv3.
"""

VERSION = "0.1.0"

import sys
from docopt import docopt
import pathlib

from bs4 import BeautifulSoup
bs = lambda x: BeautifulSoup(x, "xml")


def resource(value, resourcesPath):
    '''Finds the value of a property in an external resources file if a
    reference to it exists, otherwise just retursn the plain 'ol value.'''
    assert not value.startswith("@+id")

    if not value.startswith("@+"):
        return value

    value.replace("@+", '', 1)
    filename, key = tuple(value.split('/', 1))
    filename = resourcesPath / (filename + ".xml")
    with filename.open('r') as f:
        rsoup = bs(f).find("resources")

    return rsoup.find(name=key).string


def inheritable(value, parent, getFn):
    '''Handles parent inheritance of attribute values. value is the XML
    attribute value, parent is the object's parent, and getFn accesses the
    relevant attribute when given the parent as an argument.'''

    if value in ("match_parent", "fill_parent"):
        return getFn(parent)
    else:
        return value


class AndroidView:

    '''An android Layout or Object.'''

    self.height = self.width = None

    @staticmethod
    def fromSoup(parent, soup, resourcesPath):
        if soup.name.endswith("Layout"):
            cls = Layout
        else:
            cls = AndroidObject


class AndroidLayout(AndroidView):

    '''One of three Android layouts: LinearLayout, RelativeLayout, TableLayout.'''

    def __init__(self, parent, height, width, orientation, children, gravity=None, subGravity=None):
        self.height = inheritable(height, parent, lambda x: x.height)
        self.width = inheritable(width, parent, lambda x: x.width)
        self.orientation = orientation
        self.children = children

    @staticmethod
    def fromSoup(parent, soup, resourcesPath):
        dispatch = {
            "LinearLayout": LinearLayout,
            "TabularLayout": TabularLayout,
            "RelativeLayout": RelativeLayout,
        }
        cls = dispatch[soup.name]
        return cls.fromSoup(parent, soup, resourcesPath)


class LinearLayout(AndroidLayout):

    self.children = None

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        self.id = soup["android:id"]
        self.height = soup["android:layout_height"]
        self.width = soup["android:layout_width"]
        self.children = [ AndroidView.fromSoup(kid) for kid in soup.children ]
        # TODO

        new = cls(id, parent, height, width, orientation, children, gravity, subGravity)
        return new


class RelativeLayout(AndroidLayout):

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        raise NotImplementedError


class TableLayout(AndroidLayout):

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        raise NotImplementedError


class TableRow(AndroidLayout):

    def __init__(self, children):
        self.children = children

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        raise NotImplementedError


class AndroidObject(AndroidView):

    '''A widget/view that goes inside a Layout.'''
    pass


class Clickable(AndroidObject):

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
        text = self.resource(soup.get("android:text", None), resourcesPath)
        gravity = soup.get("android:gravity", None)

        new = cls(id, parent, height, width, text, gravity)
        return new


if __name__ == "__main__":
    args = docopt(__doc__, version=VERSION)

    if args["-v"]:
        log = print
    elif args["-l"]:
        f = open(args["LOGFILE"], "a")
        log = lambda x: print(x, file=f)
    else:
        log = lambda x: None

    layoutPath = pathlib.Path(args["LAYOUTS"])
    resourcesPath = args["VALUES"]
    if resourcesPath is None:
        log("Warning: no VALUES directory specified. Attempting to do without it.")
        resourcesPath = None
    else:
        resourcesPath = pathlib.Path(args["VALUES"])

    files = [ f for f in layoutPath.iterdir() if f.is_file() ]
    for filename in files:
        with filename.open('r') as f:
            s = bs(f)
        try:
            l = AndroidLayout.fromSoup(s)
            l.
        except NotImplementedError:
            continue

    if args["-l"]:
        f.close()
