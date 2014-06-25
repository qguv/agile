#!/usr/bin/env python3

from bs4 import BeautifulSoup
bs = lambda x: BeautifulSoup(x, "xml")


class Dip(int):
    '''Device-independent pixels.'''

    def toInches(self) -> float:
        return self / float(160)

    @classmethod
    def fromInches(cls, inches: int) -> "Dip":
        return cls(round(inches * 160))

    @classmethod
    def fromMillimeters(cls, mm: int) -> "Dip":
        inches = mm * 3.93700787402e-2
        return cls.fromInches(inches)

    @classmethod
    def fromCentimeters(cls, cm: int) -> "Dip":
        mm = cm * 10
        return cls.fromMillimeters(mm)

    @classmethod
    def fromAndroid(cls, s: str) -> "Dip":
        '''Generates a Dip value from an Android XML property.'''

        s = s.replace(' ', '')

        dispatch = {
            "dp": cls.__new__,
            "dip": cls.__new__,
            "in": cls.fromInches,
            "mm": cls.fromMillimeters,
            "cm": cls.fromCentimeters,
        }

        num = None
        for end, fn in dispatch.items():
            if s.endswith(end):
                num = s.partition(end)[0]
                break

        if num is None:
            raise ValueError

        return fn(num)


def resource(value, resourcesPath):
    '''Finds the value of a property in an external resources file if a
    reference to it exists, otherwise just returns the plain 'ol value.'''

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

    def __init__(self, height, width):
        self.height = self.width = None

    @staticmethod
    def fromSoup(parent, soup, resourcesPath):
        '''When given soup, delegates to function of same name in its
        subclasses.'''

        if soup.name.endswith("Layout"):
            cls = Layout
        else:
            cls = AndroidObject

        return cls.fromSoup(parent, soup, resourcesPath)


class AndroidLayout(AndroidView):

    '''One of three Android layouts: LinearLayout, RelativeLayout, TableLayout.'''

    def __init__(self, parent, height, width, orientation, children, gravity=None, subGravity=None):
        self.height = inheritable(height, parent, lambda x: x.height)
        self.width = inheritable(width, parent, lambda x: x.width)
        self.orientation = orientation
        self.children = children

    @staticmethod
    def fromSoup(parent, soup, resourcesPath):
        '''When given soup, delegates to function of same name in its
        subclasses.'''

        dispatch = {
            "LinearLayout": LinearLayout,
            "TabularLayout": TabularLayout,
            "RelativeLayout": RelativeLayout,
        }
        cls = dispatch[soup.name]
        return cls.fromSoup(parent, soup, resourcesPath)


class LinearLayout(AndroidLayout):

    '''An AndroidLayout which displays its children in-line. The simplest AndroidLayout.'''

    def __init__(self):
        self.children = None

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        '''Initializes a new LinearLayout from a bs4 soup object.'''

        self.id = soup["android:id"]
        self.height = soup["android:layout_height"]
        self.width = soup["android:layout_width"]
        self.children = [ AndroidView.fromSoup(kid)
                          for kid in soup.children ]
        # TODO

        new = cls(id, parent, height, width, orientation, children, gravity, subGravity)
        return new


class RelativeLayout(AndroidLayout):

    '''An AndroidLayout which displays its children relative to each-other. The
    most complicated AndroidLayout.'''

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        '''Initializes a new RelativeLayout from a bs4 soup object.'''

        raise NotImplementedError


class TableLayout(AndroidLayout):

    '''An AndroidLayout which displays its children in a table.'''

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        '''Initializes a new TableLayout from a bs4 soup object.'''

        raise NotImplementedError


class TableRow(AndroidLayout):

    '''A child of TableLayout, a TableRow holds objects and displays them
    horizontally in order.'''

    def __init__(self, children):
        self.children = children

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        '''Initializes a new TableRow from a bs4 soup object.'''

        raise NotImplementedError


class AndroidObject(AndroidView):

    '''A widget/view that goes inside a Layout.'''

    def __init__(*args):
        raise NotImplementedError

    @staticmethod
    def fromSoup(parent, soup, resourcesPath):
        '''Delegates AndroidObject initialization from a bs4 soup object to the
        proper sub-class.'''

        dispatch = {
            "Button": Button
        }

        cls = dispatch[soup.name]
        return cls.fromSoup(parent, soup, resourcesPath)


class Button(AndroidObject):

    '''Represents the button class in an android layout.'''

    def __init__(self, id, parent, height, width, text="", gravity=None):
        self.id = id
        self.parent = parent

        self.text = text

        height = Dip.fromAndroid(height)
        width = Dip.fromAndroid(width)
        self.height = inheritable(height, parent, lambda x: x.height)
        self.width = inheritable(height, parent, lambda x: x.height)

        self.gravity = gravity

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        '''Initializes a new Button from a bs4 soup object.'''

        id = soup["android:id"]
        height = soup["android:layout_height"]
        width = soup["android:layout_height"]
        text = self.resource(soup.get("android:text", None), resourcesPath)
        gravity = soup.get("android:gravity", None)

        new = cls(id, parent, height, width, text, gravity)
        return new
