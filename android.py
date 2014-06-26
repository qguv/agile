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

    if value is None:
        return

    # ID is not inheritable; this should prevent programming errors. It should
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


def inheritable(value, parent, getFn):
    '''Handles parent inheritance of attribute values. value is the XML
    attribute value, parent is the object's parent, and getFn accesses the
    relevant attribute when given the parent as an argument.'''

    if value in ("match_parent", "fill_parent"):
        return getFn(parent)
    else:
        return value


class AndroidElement:

    '''An android Layout or Object.'''

    self.id = None
    self.height = None  # None or a Dip value
    self.width = None  # None or a Dip value
    self.parent = None

    # This is an element's own gravity. Android XML would call it
    # "android:layout_gravity". Contrast with AndroidLayout.childGravity.
    self.gravity = None

    @staticmethod
    def dispatchFromSoup(parent, soup, resourcesPath):
        '''When given soup, delegates to function of same name in its
        subclasses.'''

        if soup.name.endswith("Layout"):
            cls = Layout
        else:
            cls = AndroidObject

        return cls.fromSoup(parent, soup, resourcesPath)

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        '''Should initialize a new instance from a bs4 soup object.'''

        raise NotImplementedError


class AndroidLayout(AndroidElement):

    '''One of four Android layouts: LinearLayout, TableLayout, FrameLayout,
    RelativeLayout.'''

    self.orientation = None  # "horizontal" or "vertical"
    self.children = tuple()

    # This is the default gravity of an element's children. Android XML would
    # call it "android:gravity". Contrast with AndroidElement.gravity.
    self.childGravity = None

    @staticmethod
    def dispatchFromSoup(parent, soup, resourcesPath):
        '''When given soup, delegates to function of same name in its
        subclasses.'''

        dispatch = {
            "LinearLayout": LinearLayout,
            "TabularLayout": TabularLayout,
            "FrameLayout": FrameLayout,
            "RelativeLayout": RelativeLayout,
        }
        cls = dispatch[soup.name]
        return cls.fromSoup(parent, soup, resourcesPath)


class LinearLayout(AndroidLayout):

    '''An AndroidLayout which displays its children in-line. The simplest AndroidLayout.'''

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        '''Initializes a new LinearLayout from a bs4 soup object.'''

        new = cls()

        new.id = soup["android:id"]
        new.height = soup["android:layout_height"]
        new.width = soup["android:layout_width"]
        new.children = tuple([ AndroidElement.dispatchFromSoup(kid)
                               for kid in soup.children ])

        return new


class FrameLayout(AndroidLayout):

    '''An AndroidLayout which displays its children stacked in an artifical
    Z-dimension.'''

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        '''Initializes a new FrameLayout from a bs4 soup object.'''

        raise NotImplementedError


class TableLayout(AndroidLayout):

    '''An AndroidLayout which displays its children in a table.'''

    self.children = None

    @property
    def children(self):
        return self.children

    @children.set
    def children(self, children):
        if not all([ type(child) is TableRow for child in children ]):
            m = "all children of a TableLayout must be TableRow instances"
            raise TypeError(m)
        self.children = children

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        '''Initializes a new TableLayout from a bs4 soup object.'''

        raise NotImplementedError


class TableRow(AndroidLayout):

    '''A child of TableLayout, a TableRow holds objects and displays them
    horizontally in order.'''

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        '''Initializes a new TableRow from a bs4 soup object.'''

        raise NotImplementedError


class RelativeLayout(AndroidLayout):

    '''An AndroidLayout which displays its children relative to each-other. The
    most complicated AndroidLayout.'''

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        '''Initializes a new RelativeLayout from a bs4 soup object.'''

        raise NotImplementedError


class AndroidObject(AndroidElement):

    '''A widget/view that goes inside a Layout.'''

    @staticmethod
    def dispatchFromSoup(parent, soup, resourcesPath):
        '''Delegates AndroidObject initialization from a bs4 soup object to the
        proper sub-class.'''

        dispatch = {
            "Button": Button
        }

        cls = dispatch[soup.name]
        return cls.fromSoup(parent, soup, resourcesPath)


class Button(AndroidObject):

    '''Represents the button class in an android layout.'''

    @classmethod
    def fromSoup(cls, parent, soup, resourcesPath):
        '''Initializes a new Button from a bs4 soup object.'''

        new = cls()

        new.id = soup["android:id"]

        new.text = resource(soup.get("android:text", None), resourcesPath)

        height = soup["android:layout_height"]
        height = inheritable(height, parent, lambda x: x.height)
        new.height = Dip.fromAndroid(height)

        width = soup["android:layout_width"]
        width = inheritable(width, parent, lambda x: x.width)
        new.width = Dip.fromAndroid(width)

        gravity = soup.get("android:layout_gravity", "match_parent")
        new.gravity = inheritable(width, parent, lambda x: x.childGravity)

        return new
