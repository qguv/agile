#!/usr/bin/env python3
# this file is okay to import * into devices.py

from bs4 import BeautifulSoup
import pygame.font as fonts
from functools import lru_cache as memoize
bs = lambda x: BeautifulSoup(x, "xml")


class AndroidDevice:

    '''Specifications of a device used to simulate element layout and
    position.'''

    # Values densityDpi, xdpi, and ydpi are usually equivalent.
    # If xdpi != ydpi, a densityDpi is chosen carefully.
    densityDpi = None
    xdpi = None
    ydpi = None

    # integral
    widthPixels = None
    heightPixels = None

    # floating-point
    scaledDensity = None  # accounts for font scaling

    @property
    def densityScalar(self) -> float:
        '''Determines scaling for d[i]p based on amount of true pixels per true
        inch. In other words, when multiplied by d[i]p, the quotient is length
        in true pixels.'''

        if self.densityDpi is None:
            raise ValueError("Cannot give density: no densityDpi value defined for this device.")

        return self.densityDpi / 160

    @property
    def width(self) -> "Dip":
        return Dip.fromPixels(self.widthPixels, self.densityScalar)

    @property
    def height(self) -> "Dip":
        return Dip.fromPixels(self.heightPixels, self.densityScalar)

    def textDimensions(self, text: str, *, size="14sp", font="default") -> (int, int):
        '''Determines the width of rendered text on a specific device.'''

        # FUTURE: figure out actual size and font
        # FUTURE: factor in weight

        fontFamilies = {
            "sans": "Droid Sans",
            "serif": "Droid Serif",
            "mono": "Droid Sans Mono",
            "monospaced": "Droid Sans Mono",
            "default": "Droid Sans",
        }

        fontFamily = fontFamilies.get(font.lower(), fontFamilies["default"])

        size = Dip.fromAndroid(size)
        size = size.toPoints()
        print("\n{} point font\n".format(size))  # DEBUG

        return self._textDimensions(text, size, font)

    @memoize()
    def _textDimensions(self, text, size: "points", fontFamily: str) -> (int, int):
        '''Determines the width of rendered text on a specific device. Don't
        call this directly; use a function to normalize Dip and font such that
        no errors would be raised.'''

        # FUTURE: factor in weight

        print("Calculating...")  # DEBUG
        fonts.init()
        font = fonts.SysFont(fontFamily, size)

        width, height = font.size(text)

        return (width, height)


class Dip(int):

    '''Device-independent pixels. Use the value directly if you want a DIP
    value. Otherwise, use a method beginning "to" to help you out.'''

    def toInches(self) -> float:
        return self / float(160)

    def toPoints(self) -> int:
        points = self.toInches() * 72
        points = int(round(points))
        return points

    def toPixels(self, densityScalar: float) -> int:
        return int(round(self * densityScalar))

    @classmethod
    def fromPixels(cls, pixels: int, densityScalar: float) -> "Dip":
        return cls(round(pixels / densityScalar))

    @classmethod
    def fromSp(cls, sp: int) -> "Dip":
        '''Let's pretend it's Dip for now.'''
        # FUTURE: make this actually calculate scale
        return cls(sp)

    @classmethod
    def fromInches(cls, inches: "number") -> "Dip":
        return cls(round(inches * 160))

    @classmethod
    def fromPoints(self, points: int) -> int:
        inches = points / 72
        return self.fromInches(inches)

    @classmethod
    def fromPicas(self, picas: int) -> int:
        inches = picas / 6
        return self.fromInches(inches)

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

        new = lambda x: cls.__new__(cls, x)

        dispatch = {
            "dp": new,
            "dip": new,

            # FUTURE: make these actually calculate scale
            "sp": new,
            "sip": new,

            "in": cls.fromInches,
            "mm": cls.fromMillimeters,
            "cm": cls.fromCentimeters,
            "pt": cls.fromPoints,
            "pc": cls.fromPicas,
        }

        num = None
        for end, fn in dispatch.items():
            if s.endswith(end):
                num = int(s.partition(end)[0])
                break

        if num is None:
            raise ValueError("can't figure out Dip value for {}".format(s))

        return fn(num)


def resource(value, resourcesPath):
    '''Finds the value of a property in an external resources file if a
    reference to it exists.
    If not applicable, just pipes the value on through.'''

    if value is None:
        return

    # ID is not inheritProperty; this should prevent programming errors. It should
    # be stripped production and should be considered DEBUG.
    assert not value.startswith("@+id")

    if not value.startswith("@+"):
        return value

    value.replace("@+", '', 1)
    filename, key = tuple(value.split('/', 1))
    filename = resourcesPath / (filename + ".xml")
    with filename.open('r') as f:
        rsoup = bs(f).find("resources")

    return rsoup.find(name=key).string


def inheritProperty(value, parent, getFn):
    '''Handles parent inheritance of attribute values. value is the XML
    attribute value, parent is the object's parent, and getFn accesses the
    relevant attribute when given the parent as an argument.
    If not applicable, complains.'''

    if value in ("match_parent", "fill_parent"):
        return getFn(parent)
    else:
        raise AttributeError("value is unique, not inheritProperty")


def wrappable(width: str, height: str, text: str, device: AndroidDevice, **kwargs) -> (str, str):
    '''Handles automatic "resize to fit text" on Buttons and the like.
    If not applicable, just pipes the value on through.'''

    '''
     ________
    |        |
    | Button |
    |________|
    '''


    if "wrap_content" in (width, height):
        width_text, height_text = device.textDimensions(text, **kwargs)

        if height == "wrap_content":
            # a free line above, a free line below, and a text line
            height = height_text * 3

        if width == "wrap_content":
            # the width of the text plus half of the height on both sides
            width = width_text + height_text

    return (width, height)


class AndroidElement:

    '''An android Layout or Object.'''

    id = None
    height = None  # None or a Dip value
    width = None  # None or a Dip value
    parent = None

    # This is an element's own gravity. Android XML would call it
    # "android:layout_gravity". Contrast with AndroidLayout.childGravity.
    gravity = None

    @staticmethod
    def dispatchFromSoup(parent, soup, resourcesPath, *, device=None):
        '''When given soup, delegates to function of same name in its
        subclasses.'''

        if parent is None:
            parent = device

        if soup.name.endswith("Layout"):
            cls = AndroidLayout
        else:
            cls = AndroidObject

        return cls.dispatchFromSoup(parent, soup, resourcesPath, device=device)

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath, *, device=None):
        '''Should initialize a new instance from a bs4 soup object.'''

        raise NotImplementedError(cls)


class AndroidLayout(AndroidElement):

    '''One of four Android layouts: LinearLayout, TableLayout, FrameLayout,
    RelativeLayout.'''

    orientation = None  # "horizontal" or "vertical"
    children = tuple()

    # This is the default gravity of an element's children. Android XML would
    # call it "android:gravity". Contrast with AndroidElement.gravity.
    childGravity = None

    @staticmethod
    def dispatchFromSoup(parent, soup, resourcesPath, *, device=None):
        '''When given soup, delegates to function of same name in its
        subclasses.'''

        dispatch = {
            "LinearLayout": LinearLayout,
            "TableLayout": TableLayout,
            "FrameLayout": FrameLayout,
            "RelativeLayout": RelativeLayout,
        }
        cls = dispatch[soup.name]
        return cls.fromSoup(parent, soup, resourcesPath, device=device)

def findChildren(commonParent, soupChildren: "output from soup.children", resourcesPath, *, device=None) -> tuple("children"):
    children = []
    for kid in soupChildren:
        try:
            kid = AndroidElement.dispatchFromSoup(commonParent, kid, resourcesPath, device=device)
            children.append(kid)
        except AttributeError:
            # the object is a string or something weird that's not soup
            continue
        except NotImplementedError:
            continue
    return tuple(children)


class LinearLayout(AndroidLayout):

    '''An AndroidLayout which displays its children in-line. The simplest AndroidLayout.'''

    @property
    def takenWidth(self):
        return sum([ child.width for child in self.children ])

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath, *, device=None):
        '''Initializes a new LinearLayout from a bs4 soup object.'''

        new = cls()

        new.id = soup.get("android:id", None)
        new.height = soup("android:layout_height", None)
        new.width = soup("android:layout_width", None)

        new.parent = parent

        new.children = findChildren(new, soup.children, resourcesPath, device=device)

        return new

    def area(self):
        return self.height * self.width

    def buttonRatio(self):
        buttonArea = sum(( kid.area() for kid in self.children if type(kid) == Button ))
        return buttonArea / self.area()



class FrameLayout(AndroidLayout):

    '''An AndroidLayout which displays its children stacked in an artifical
    Z-dimension.'''

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath, *, device=None):
        '''Initializes a new FrameLayout from a bs4 soup object.'''

        raise NotImplementedError(cls)


class TableLayout(AndroidLayout):

    '''An AndroidLayout which displays its children in a table.'''

    _children = None
    children = property(lambda self: self._children)  # getter

    @children.setter
    def _(self, children):
        if not all([ type(child) is TableRow for child in children ]):
            m = "all children of a TableLayout must be TableRow instances"
            raise TypeError(m)
        self.children = children

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath, *, device=None):
        '''Initializes a new TableLayout from a bs4 soup object.'''

        raise NotImplementedError(cls)


class TableRow(AndroidLayout):

    '''A child of TableLayout, a TableRow holds objects and displays them
    horizontally in order.'''

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath, *, device=None):
        '''Initializes a new TableRow from a bs4 soup object.'''

        raise NotImplementedError(cls)


class RelativeLayout(AndroidLayout):

    '''An AndroidLayout which displays its children relative to each-other. The
    most complicated AndroidLayout.'''

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath, *, device=None):
        '''Initializes a new RelativeLayout from a bs4 soup object.'''

        raise NotImplementedError(cls)


class AndroidObject(AndroidElement):

    '''A widget/view that goes inside a Layout.'''

    @staticmethod
    def dispatchFromSoup(parent, soup, resourcesPath, device=None):
        '''Delegates AndroidObject initialization from a bs4 soup object to the
        proper sub-class.'''

        dispatch = {
            "Button": Button
        }

        cls = dispatch.get(soup.name, UnknownObject)
        return cls.fromSoup(parent, soup, resourcesPath, device=device)


class UnknownObject(AndroidObject):

    '''Called when we don't know about the properties of the AndroidObject but
    we know it exists.'''

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath, *, device=None):
        '''Does its best to tell us as much as it can about an object we don't
        know anything about.'''

        new = cls()

        width = soup["android:layout_width"]
        height = soup["android:layout_height"]

        try:
            text = soup["android:text"]
            wrappable(width, height, text, device)
        except KeyError:
            # no text in soup
            print(width, height)

        try:
            new.height = inheritProperty(height, parent, lambda x: x.height)
        except AttributeError:
            # handling uninheritable property
            new.height = Dip.fromAndroid(height)
        except KeyError:
            # handling soup access error
            print("Couldn't find height.")

        try:
            new.width = inheritProperty(width, parent, lambda x: x.width)
        except AttributeError:
            # handling uninheritable property
            new.width = Dip.fromAndroid(width)
        except KeyError:
            # handling soup access error
            print("Couldn't find width.")


class Button(AndroidObject):

    '''Represents the button class in an android layout.'''

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath, *, device=None):
        '''Initializes a new Button from a bs4 soup object.'''

        new = cls()

        new.id = soup["android:id"]

        new.text = resource(soup.get("android:text", None), resourcesPath)

        width = soup["android:layout_width"]
        height = soup["android:layout_height"]

        # FUTURE: implement fonts
        width, height = wrappable(width, height, new.text, device)

        try:
            new.width = inheritProperty(width, parent, lambda x: x.width)
        except AttributeError:
            new.width = Dip.fromAndroid(width)

        try:
            new.height = inheritProperty(height, parent, lambda x: x.height)
        except AttributeError:
            new.height = Dip.fromAndroid(height)

        gravity = soup.get("android:layout_gravity", "match_parent")
        try:
            new.gravity = inheritProperty(width, parent, lambda x: x.childGravity)
        except AttributeError:
            new.gravity = gravity

        return new

    def area(self):
        return self.width * self.height
