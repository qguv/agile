#!/usr/bin/env python3

from devices import galaxyS3

print("\nTESTING TEXT DIMENSION PROBING")
w, h = galaxyS3.textDimensions("Hello, world!")
print(w, h)
w, h = galaxyS3.textDimensions("Hello, world!", size="8cm")
print(w, h)
w, h = galaxyS3.textDimensions("Hello, world!", size="227pt")
print(w, h)

print("\nTESTING LEXER")
import android
android.Android


print("\nTESTING BUTTON DIMENSION CALCULATION")

print("\nTESTING AREA CALCULATION")
