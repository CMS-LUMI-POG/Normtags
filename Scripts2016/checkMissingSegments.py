#!/usr/bin/env python

import json
import argparse

# Take a csv output file from brilcalc and average the pileup in that file.

# Parse input arguments.
parser = argparse.ArgumentParser()
parser.add_argument('infile', help='First input file to compare.')
parser.add_argument('infile2', help='Second input file to compare.')
args = parser.parse_args()

valid_lumisections = {}
# Read in current normtag for the luminometers and populate them in
# the hash valid_lumisections[l].
for f in [args.infile, args.infile2]:
    valid_lumisections[f] = {}
    with open(f, 'r') as jsonFile:
        validPeriods = json.load(jsonFile)
    for entry in validPeriods:
        runHash = entry[1]
        for run in runHash.keys():
            r = int(run)
            if r not in valid_lumisections[f]:
                valid_lumisections[f][r] = set()
            ranges = runHash[run]
            for thisRange in ranges:
                startLS = thisRange[0]
                endLS = thisRange[1]
                for i in range(startLS, endLS+1):
                    valid_lumisections[f][r].add(i)

# Now look for things in one and not the other.
inMissingRange = False
totalMissingLS = 0
for r in sorted(valid_lumisections[args.infile].keys()):
    for ls in sorted(valid_lumisections[args.infile][r]):
        if not inMissingRange and (r not in valid_lumisections[args.infile2] or ls not in valid_lumisections[args.infile2][r]):
            inMissingRange = True
            startRun = r
            startLS = ls
        if inMissingRange and r in valid_lumisections[args.infile2] and ls in valid_lumisections[args.infile2][r]:
            print str(startRun)+":"+str(startLS)+" to "+str(lastRun)+":"+str(lastLS)+" in "+args.infile+" but not in "+args.infile2
            inMissingRange = False
        if inMissingRange:
            totalMissingLS += 1
        lastRun = r
        lastLS = ls

# don't forget to check last range
if inMissingRange:
    print str(startRun)+":"+str(startLS)+" to "+str(lastRun)+":"+str(lastLS)+" in "+args.infile+" but not in "+args.infile2
print "Total of",totalMissingLS,"LS missing"

# for r in sorted(valid_lumisections[args.infile].keys()):
#     for ls in sorted(valid_lumisections[args.infile][r]):
#         if r not in valid_lumisections[args.infile2] or ls not in valid_lumisections[args.infile2][r]:
#             print r,ls,"in",args.infile,"but not in",args.infile2
