#!/usr/bin/python

import os, sys, csv, re

# This script analyzes the results of getNBX.py and separates the fills into four categories: fills where all
# four sources agree, fills where the WBM target number disagrees with the other three, fills where the WBM
# colliding number disagrees with the other three, and fills with more substantial disagreement. In addition
# it also catches one additional case where the beam number is affected by the off-by-one bug that is present
# in many fills in 2016 and afterwards. Note that this last category is not exclusive, so fills can appear
# both in it and one of the other categories.  It also writes the final authoritative number to the csv file,
# taking the luminometer number as authoritative.

if len(sys.argv) > 1:
    infile = sys.argv[1]
else:
    print "Usage: "+sys.argv[0]+" <infile>"
    sys.exit(1)

# Get the year number from the input file. Note: only works for LHC fills in the 21st century.
result = re.search("(20\d\d)", infile)
if result:
    outfile = "NBX_perFill_"+result.group(1)+".csv"
else:
    outfile = "NBX_perFill.csv"

allGood = []
wbmTargetBad = []
wbmCollidingBad = []
otherBad = []
beamOffByOne = []

with open(infile) as inputFile:
    outputFile = open(outfile, "w")

    reader = csv.reader(inputFile, delimiter=",")
    for row in reader:
        
        # Skip any rows which don't contain a comma (these should just be warning messages)
        if len(row) == 1:
            continue

        # Fields are: fill number, WBM target, WBM colliding, beam, luminometers
        # We can't do this as a big if-else since things can fall in more than one category, so just do it
        # condition-by-condition.
        putInCategory = False
        if (row[1] == row[4] and row[2] == row[4] and row[3] == row[4]):
            allGood.append(row[0])
            putInCategory = True
        if (row[1] != row[4] and row[2] == row[4] and (row[3] == row[4] or int(row[3])+1 == int(row[4]))):
            wbmTargetBad.append(row[0])
            putInCategory = True
        if (row[1] == row[4] and row[2] != row[4] and (row[3] == row[4] or int(row[3])+1 == int(row[4]))):
            wbmCollidingBad.append(row[0])
            putInCategory = True
        if (int(row[3])+1 == int(row[4]) and (row[1] == row[4] or row[2] == row[4])):
            beamOffByOne.append(row[0])
            putInCategory = True
        if not putInCategory:
            otherBad.append(",".join(row))

        outputFile.write(row[0]+","+row[4]+"\n")

    outputFile.close()

print "All good:"
print ", ".join(allGood)
print "WBM target bad:"
print ", ".join(wbmTargetBad)
print "WBM colliding bad:"
if len(wbmCollidingBad) > 0:
    print ", ".join(wbmCollidingBad)
else:
    print "None"
print "Beam off by one:"
if len(beamOffByOne) > 0:
    print ", ".join(beamOffByOne)
else:
    print "None"
if otherBad:
    print "More substantial disagreements:"
    print "\n".join(otherBad)

print "Wrote output to", outfile

