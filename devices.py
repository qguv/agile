#!/usr/bin/env python3

import android

galaxyS3 = AndroidDevice()
with galaxyS3 as a:

    a.densityDpi = 306

    a.xdpi = a.ydpi = a.densityDpi
    a.scaledDensity = a.densityDpi

    a.widthPixels, a.heightPixels = 720, 1280

