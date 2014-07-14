#!/usr/bin/env python3

"""agile, the Android Graphical Interface LEXer

Usage:
  agile.py tags [options] (-o CSV) LAYOUTS [--values VALUES]
  agile.py tags [options] (-o CSV) (--repo REPOSITORY)
  agile.py (-h | --help | help)
  agile.py --version

Arguments:
  CSV                Path to output CSV.
  LAYOUTS            Path to res/layouts.
  VALUES             Path to res/values.
  REPOSITORY         Path to a folder of Android packages.

Options:
  tags               Count tags.
  -l LOGFILE         Log output to a file.
  -v                 Increase verbosity.
  -h --help          Show this screen.
  --version          Display version.

agile is written by Quint Guvernator and licensed by the GPLv3."""

VERSION = "indev"

import sys
from docopt import docopt
import pathlib
import statistics
import csv
import os
from itertools import chain

from bs4 import BeautifulSoup
bs = lambda x: BeautifulSoup(x, "xml")


def countLayoutButtons(soup: "soup from an XML layout") -> int:
    '''Count how many buttons are defined in a layout.'''
    return len(soup("Button"))


def countTags(soup: "soup from an XML layout") -> dict:
    '''Return a dictionary listing the freqency of each tag type by name.'''

    tagCount = dict()

    tags = soup.find_all(True) #TODO

    for tag in tags:
        # increase int by one
        name = tag.name
        if tag.name is None:
            continue
        key = "tag_{}".format(name)

        oldvalue = int(tagCount.get(name, 0))
        tagCount[key] = oldvalue + 1

    return tagCount


def countAppButtons(layoutsPath: pathlib.Path) -> [int, ...]:
    '''Count how many buttons are defined in each layout in an application's
    layouts directory.'''

    layouts, _ = appSoup(layoutsPath)
    return [ countLayoutButtons(soup) for soup in layouts ]


def countAppTags(layoutsPath: pathlib.Path) -> dict:
    '''Returns a combined tag frequency dictionary for all layouts in an
    application's layouts directory.'''

    # we'll get all the app's layouts as a list of soup
    layouts, name = appSoup(layoutsPath)

    alltags = dict()
    for soup in layouts:

        # we can get a dictionary of tags in each layout with countTags
        # we'll make a running total of each in the "total" dictionary
        newtags = countTags(soup)

        # combine all dictionaries in all layouts

        # combine unique keys
        newkeys = set(newtags.keys())
        oldkeys = set(alltags.keys())
        keys = oldkeys.union(newkeys)

        # combine all values
        for k in keys:
            oldvalue = int(alltags.get(k, 0))
            newvalue = int(newtags.get(k, 0))
            alltags[k] = oldvalue + newvalue

    # throw the package location in there and we're all done
    alltags["package"] = name
    return alltags


def countLayouts(layoutsPath: pathlib.Path) -> int:
    '''Counts how many layouts are defined.'''
    return len([ f for f in layoutsPath.iterdir() if f.is_file() ])


def layoutSoup(layoutPath: pathlib.Path) -> "soup":
    '''Make soup from a single layout.'''

    with layoutPath.open('r') as f:
        s = bs(f)
    return s


def appSoup(layoutsPath: pathlib.Path) -> ["soup", ...]:
    '''Make soup from each layout in an application's layouts directory.'''

    apps = [ f for f in layoutsPath.iterdir() if f.is_file() ]
    name = str(layoutsPath)
    layouts = [ layoutSoup(f) for f in apps ]
    return layouts, name


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

    # plain ratings
    stats = { "star_{}".format(i + 1): r for i, r in enumerate(ratings) }

    # the mean
    stats["star_mean"] = mean

    return stats


def calcButtonStats(buttons: list) -> dict:

    stats = {}

    for k, v in calcStats(buttons).items():
        label = "button_{}".format(k)
        stats[label] = v

    return stats


def writeStats(outFile: pathlib.Path, *statsDicts: (dict, ...)) -> None:

    # combine feature and rating stats into a row of statistics
    statsItems = ( d.items() for d in statsDicts )
    stats = dict(chain(*statsItems))

    # neither unique entries nor order matters
    header = set(stats.keys())

    # add other entries if already in the file
    if outFile.exists():
        with outFile.open('r') as f:
            r = csv.DictReader(f)
            entries = list(r)

            # add headers already in file
            header = header.union(r.fieldnames)

        try:
            os.remove(outFile.as_posix())
        except OSError as e:
            print("Error: {} - {}".format(e.filename, str(e)))
    else:
        entries = []

    # add current row of statistics
    entries.append(stats)

    # write 'em all
    with outFile.open('w') as f:
        header = sorted(header)
        w = csv.DictWriter(f, header)
        w.writeheader()
        w.writerows(entries)

def _die(f, code=0):
    '''Closes open files and quits.'''
    if f is not None:
        f.close()
    sys.exit(code)

def _getArgDirs(args, log=lambda x: None) -> ("res/layouts", "res/values")
    '''Determines input and output files from command-line arguments.'''
    layoutPath = pathlib.Path(args["LAYOUTS"])
    resourcesPath = args["VALUES"]
    if resourcesPath is None:
        log("Warning: no VALUES directory specified.")
        log("Attempting to do without it.")
        resourcesPath = None
    else:
        resourcesPath = pathlib.Path(args["VALUES"])
    return (layoutPath, resourcesPath)

def _getRepoDirs("repo path") -> [("res/layouts", "res/values"), ...]:
    pass #TODO

def _getLogFn(args) -> ("function", file):
    '''Check CLI args to determine the log function.'''
    if args["-v"]:
        return (print, None)
    elif args["-l"]:
        f = open(args["LOGFILE"], "a")
        log = lambda x: print(x, file=f)
        return (log, f)
    else:
        return (lambda x: None, None)

if __name__ == "__main__":
    args = docopt(__doc__, version=VERSION)

    # How do we want to log?
    log, f = _getLogFn()

    # How are we getting our data?
    if args["--repo"]:
        dirs = _getRepoDirs(args["--repo"])
    else:
        dirs = [_getArgDirs(args, log=log)]

    # Where are our independent variable stats coming from?
    if args["tags"]:
        stats = countAppTags(layoutPath)

    # calculate dependent variable (evaluative metric) stats
    ratingStats = calcRatingStats(getRating(layoutPath))

    # Where are our stats going?
    outFile = pathlib.Path(args["-o"])

    # other statistics to add
    layoutCount = { "layoutCount": countLayouts(layoutPath) }

    # put all statistics in the file
    writeStats(outFile, stats, ratingStats, layoutCount)

    # kill files if we've got 'em
    _die(f)
