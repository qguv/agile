#!/usr/bin/env python3

"""agilex, the Android Graphical Interface LEXer

Usage:
  agilex.py [options] LAYOUTS [VALUES]
  agilex.py (-h | --help | help)
  agilex.py --version

Arguments:
  LAYOUTS     Path to res/layouts.
  VALUES      Path to res/values.

Options:
  --no-zero-layouts  Ignore layouts with zero buttons.
  --no-zero-apps     Ignore apps with zero buttons.
  -c CSV             Write stats to a CSV file.
  -l LOGFILE         Log output to a file.
  -v                 Increase verbosity.
  -h --help          Show this screen.
  --version          Display version.

agilex is written by Quint Guvernator and licensed by the GPLv3."""

VERSION = "0.1.0"

import sys
from docopt import docopt
import pathlib
import statistics
import csv
import os
from itertools import chain

from bs4 import BeautifulSoup
bs = lambda x: BeautifulSoup(x, "xml")

import android  # local


def countLayoutButtons(soup):
    '''Given soup of an XML file, count how many buttons are defined.'''
    return len(soup("Button"))


def countAppButtons(layoutPath: pathlib.Path) -> list:
    files = [ f for f in layoutPath.iterdir() if f.is_file() ]
    buttons = []

    for filename in files:
        with filename.open('r') as f:
            s = bs(f)
        buttons.append(countLayoutButtons(s))

    return buttons


def getRating(layoutsPath: pathlib.Path) -> (list, int):
    '''Gets a rating count and an average rating. The average rating is
    returned as element [0], and the star counts are returned as their
    respective elements, 1 to and including 5.'''

    p = layoutsPath.resolve()
    root = layoutsPath.parts[0]

    while "rating.txt" not in [ f.name for f in p.iterdir() ]:
        parent = p.parent
        if p == parent:
            raise FileNotFoundError
        p = parent

    p = p / "rating.txt"
    out = [0] * 6

    with p.open('r') as f:

        # ratings
        for i in range(1, 6):
            out[i] = int(f.readline().strip())

        # checking against total
        if int(f.readline().strip()) != sum(out):
            raise ValueError("rating.txt reports wrong total value")

        # average
        out[0] = float(f.readline())

    return out


def emptyStats() -> dict:
    stats = {
        "mean": 0,
        "median": 0,
        "mode": 0,
        "min": 0,
        "max": 0,
        "pvariance": "NA",
        "stdev": "NA",
    }
    return stats


def calcStats(vector: list) -> dict:

    statFns = {
        "mean": statistics.mean,
        "median": statistics.median,
        "mode": statistics.mode,
        "min": min,
        "max": max,
        "pvariance": statistics.pvariance,
        "stdev": statistics.stdev,
    }

    stats = {}

    for k, fn in statFns.items():
        try:
            stats[k] = fn(vector)
        except statistics.StatisticsError:
            stats[k] = "NA"

    return stats


def calcRatingStats(ratings: list) -> dict:

    mean = ratings[0]
    ratings = ratings[1:]

    stats = {}

    for k, v in calcStats(ratings).items():

        label = "rating_{}".format(k)

        if k == "mean":
            # mean doesn't mean what it's supposed to mean here. we'll replace it
            # with our own.
            stats[label] = mean
            continue

        stats[label] = v

    # add the plain 'ol ratings
    for i, r in enumerate(ratings):
        label = "{} stars".format(i + 1)
        stats[label] = r

    return stats


def calcButtonStats(buttons: list) -> dict:

    stats = {}

    for k, v in calcStats(buttons).items():
        label = "button_{}".format(k)
        stats[label] = v

    return stats


def writeStats(outFile: pathlib.Path, *statsDicts: (dict, ...)) -> None:

    statsItems = ( d.items() for d in statsDicts )

    # combine buttonStats and ratingStats
    stats = dict(chain(*statsItems))

    # add other entries if already in the file
    entries = []
    if outFile.exists():
        with outFile.open('r') as f:
            r = csv.DictReader(f)
            entries.extend(list(r))
        try:
            os.remove(outFile.as_posix())
        except OSError as e:
            print("Error: {} - {}".format(e.filename, str(e)))

    # add current entry
    entries.append(stats)

    # write 'em all
    with outFile.open('w') as f:
        header = list(stats.keys())
        header.sort()
        w = csv.DictWriter(f, header)
        w.writeheader()
        w.writerows(entries)


def die():
    if args["-l"]:
        f.close()
    sys.exit()

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

    if args["-c"]:
        buttons = countAppButtons(layoutPath)
        if args["--no-zero-layouts"]:
            buttons = [ x for x in buttons if x > 0 ]

        if len(buttons) != 0:
            buttonStats = calcButtonStats(buttons)
        else:
            if args["--no-zero-apps"]:
                die()
            else:
                buttonStats = emptyStats()

        ratingStats = calcRatingStats(getRating(layoutPath))
        outFile = pathlib.Path(args["-c"])
        writeStats(outFile, buttonStats, ratingStats)

    die()
