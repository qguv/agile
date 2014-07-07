#!/usr/bin/env python3

from pathlib import Path

import android
import agilex
from devices import galaxyS3

print("\nTESTING TEXT DIMENSION PROBING")
w, h = galaxyS3.textDimensions("Hello, world!")
print(w, h)
w, h = galaxyS3.textDimensions("Hello, world!", size="8cm")
print(w, h)
w, h = galaxyS3.textDimensions("Hello, world!", size="227pt")
print(w, h)

print("\nTESTING LEXER")

xmlLayouts = agilex.appSoup(Path("/home/qguvernator/fdroid/org.torproject.android/src/res/layout/"))
layouts = []

for layout in xmlLayouts:
    layouts.append(android.AndroidElement.dispatchFromSoup(None, layout, None, device=galaxyS3))

print("\nTESTING BUTTON DIMENSION CALCULATION")

print("\nTESTING AREA CALCULATION")
