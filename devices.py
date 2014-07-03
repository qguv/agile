#!/usr/bin/env python3

from android import *  # local

galaxyS3 = AndroidDevice()
galaxyS3.densityDpi = 306

galaxyS3.xdpi = galaxyS3.ydpi = galaxyS3.densityDpi
galaxyS3.scaledDensity = galaxyS3.densityDpi

galaxyS3.widthPixels, galaxyS3.heightPixels = 720, 1280
# and the screen is 6 by 10 1/3 inches, if anyone was wondering

