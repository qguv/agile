#!/usr/bin/env python3

"""agile, the Android Graphical Interface LExer

Usage:
  agile.py tags [options] (-o CSV) LAYOUTS [--values VALUES]
  agile.py tags [options] (-o CSV) (--repo REPOSITORY) (--dirlist DIRLIST [--generate])
  agile.py (-h | --help | help)
  agile.py --version

Arguments:
  CSV         Path to output CSV.
  LAYOUTS     Path to res/layouts.
  VALUES      Path to res/values.
  REPOSITORY  Path to a folder of Android packages.
  DIRLIST     Path to the output of getRepoDirs or getArgDirs.

Options:
  tags        Count tags.
  -l LOGFILE  Log output to a file.
  --generate  Actually run getRepoDirs or getArgDirs and save it to DIRLIST.
  -v          Increase verbosity.
  -h --help   Show this screen.
  --version   Display version.

agile is written by Quint Guvernator and licensed by the GPLv3."""

VERSION = "indev"

import sys
from docopt import docopt
import pathlib
import statistics
import csv
import os
from itertools import chain
from subprocess import check_call

from bs4 import BeautifulSoup
bs = lambda x: BeautifulSoup(x, "xml")

def echo(x):
    space = (len(x) - 80) * " "
    _echo(x + space)
    _wipe()

def _echo(x):
    call = ["echo", "-n", x]
    check_call(call)

def _wipe():
    check_call(["echo", "-en", r"\e[0K\r"])

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

def countAppTags(layoutsPaths: [pathlib.Path, ...]) -> dict:
    '''Returns a combined tag frequency dictionary for all layouts in an
    application's layouts directory.'''

    # we'll get all the app's layouts as a list of soup
    layouts = []
    for l in layoutsPaths:
        layouts.extend(appSoup(l))

    alltags = dict()
    for soup in layouts:

        # we can get a dictionary of tags in each layout with countTags
        # we'll make a running total of each in the "alltags" dictionary
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
    alltags["package"] = str(layoutsPaths[0])

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

    layouts = []
    errors = 0
    for f in apps:
        try:
            layouts.append(layoutSoup(f))
        except UnicodeDecodeError:
            errors += 1

    if errors != 0:

        if errors == 1:
            plural = ''
        else:
            plural = 's'

        print("\n{} Unicode decode error{} in {}".format(errors, plural, layoutsPath))

    return layouts

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

def readAndTrash(inFile: pathlib.Path) -> (set, [dict, ...]):
    '''Reads in a CSV full of statistics and gives a set of headers and a list
    of entries (dictionaries with key=columnName).'''

    # no file, no entries
    if not inFile.exists():
        return (None, None)

    with inFile.open('r') as f:
        r = csv.DictReader(f)
        entries = list(r)
        header = set(r.fieldnames)

    if len(entries) == 0:
        raise OSError("Couldn't read from file. Delete it if it's empty.")

    try:
        os.remove(outFile.as_posix())
    except OSError as e:
        print("Error: {} - {}".format(e.filename, str(e)))

    return (header, entries)

def dictCombine(*dictionaries) -> dict:
    '''Combines dictionaries.'''

    dItems = ( d.items() for d in dictionaries )
    return dict(chain(*dItems))

def writeStats(outFile: pathlib.Path, entries: [dict]) -> None:

    # add other entries if already in the file
    header, oldEntries = readAndTrash(outFile)

    if oldEntries is None:
        print("Read a blank CSV file. Ignoring it.")
    else:
        entries.extend(oldEntries)

    if header is None:
        header = set()

    for d in entries:
        header = header.union(d.keys())

    # write 'em all
    with outFile.open('w') as f:
        header = sorted(header) #DEBUG
        w = csv.DictWriter(f, header)
        w.writeheader()
        w.writerows(entries)

def _die(f, code=0):
    '''Closes open files and quits.'''
    if f is not None:
        f.close()
    sys.exit(code)

def _getArgDirs(args, log=lambda x: None) -> ("res/layouts", "res/values"):
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

def _getRepoDirs(repoDir: "repo path") -> [(["res/layout", ...], ["res/values", ...]), ...]:
    repos = []
    print("Finding applications in repository...")
    for i, repo in enumerate(repoDir.iterdir()):
        echo("{:4} found: {}".format(i, repo))
        repos.append(repo)
    print()

    paths = []

    repo_count = len(repos)

    print("Finding application layouts...")
    for i, repo in enumerate(repos):
        echo("{:3}% {}".format(i * 100 // repo_count, repo))
        try:
            layouts = list(repo.glob("**/res/layout"))
            values = list(repo.glob("**/res/values"))
        except OSError as e:
            print("\nBroken app!", e.filename, str(e) + '\n')
            continue

        layouts = [ l for l in layouts if ".hg" not in l.parts ]
        values = [ l for l in values if ".hg" not in l.parts ]
        paths.append((layouts, values))

    print()
    return paths

def _getLogFn(args) -> ("function", "file"):
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

    if args["--dirlist"]:
        import pickle

    # How do we want to log?
    log, f = _getLogFn(args)

    if args["--dirlist"] and not args["--generate"]:
        print("Using application layouts in", args["DIRLIST"] + ".")
        with open(args["DIRLIST"], 'rb') as f:
            dirs = pickle.load(f)
    else:
        # How are we getting our data?
        if args["--repo"]:
            dirs = _getRepoDirs(pathlib.Path(args["REPOSITORY"]))
        else:
            print("Finding application layouts...")
            dirs = [_getArgDirs(args, log=log)]

    if args["--dirlist"] and args["--generate"]:
        print("Pickling to", args["DIRLIST"] + "...")
        with open(args["DIRLIST"], 'wb') as f:
            pickle.dump(dirs, f)
        print("100%", str(pathlib.Path(args["DIRLIST"])))

    allDirs = len(dirs)

    # start a list of dicts, which represent CSV rows, which represent apps
    entries = []
    print("Counting application layout tags...")
    for i, pair in enumerate(dirs):
        layoutPaths, resourcesPaths = pair
        echo("{:3}%".format(i * 100 // allDirs))

        if len(layoutPaths) == 0:
            continue

        # Where are our independent variable stats coming from?
        if args["tags"]:
            stats = countAppTags(layoutPaths)

        # calculate dependent variable (evaluative metric) stats. it doesn't
        # matter which layoutPath we use to find the rating since they're all
        # looking for a parent anyway
        try:
            ratingStats = calcRatingStats(getRating(layoutPaths[0]))
        except IndexError:
            try:
                ratingStats = calcRatingStats(getRating(resourcePaths[0]))
            except IndexError:
                print("Can't get rating!")
                continue

        # other statistics to add
        layoutCount = (countLayouts(p) for p in layoutPaths)
        layoutCount = { "layoutCount": sum(layoutCount) }

        entries.append(dictCombine(stats, ratingStats, layoutCount))

    print()

    # Where are our stats going?
    outFile = pathlib.Path(args["CSV"])

    print("Writing {} entries to file...".format(len(entries)))
    writeStats(outFile, entries)
    print("Done. Closing open files...")
    _die(f)
    print("Done.")
