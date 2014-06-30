#!/usr/bin/env python3

# has been designed to fit into one namespace
from android import *

galaxyS3 = AndroidDevice()
galaxyS3.densityDpi = 306

galaxyS3.xdpi = galaxyS3.ydpi = galaxyS3.densityDpi
galaxyS3.scaledDensity = galaxyS3.densityDpi

galaxyS3.widthPixels, galaxyS3.heightPixels = 720, 1280

