#!/usr/bin/python

import os, sys, csv

# This script postprocesses the getNBX.py results for 2016. It is much the same as the 2015 script but catches
# one additional case where the beam number is affected by the off-by-one bug that is present in many 2016
# fills. Note that a fill can appear in more than one category (if both one of the WBM numbers is inaccurate
# and the off-by-one bug is present).

infile = "results_2016_final.txt"
if len(sys.argv) > 1:
    infile = sys.argv[1]

outfile = "NBX_perFill_2016.csv"

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
print ", ".join(wbmCollidingBad)
print "Beam off by one:"
print ", ".join(beamOffByOne)
if otherBad:
    print "More substantial disagreements:"
    print "\n".join(otherBad)

print "Wrote output to", outfile

