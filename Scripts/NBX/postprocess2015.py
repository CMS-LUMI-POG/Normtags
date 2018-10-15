#!/usr/bin/python

import os, sys, csv

# This script analyzes the results of getNBX.py for the 2015 data and separates the fills into four
# categories: fills where all four sources agree, fills where the WBM target number disagrees with the other
# three, fills where the WBM colliding number disagrees with the other three, and fills with more substantial
# disagreement. It also writes the final authoritative number to the csv file, taking the luminometer number
# as authoritative.

infile = "results_2015_final.txt"
if len(sys.argv) > 1:
    infile = sys.argv[1]

outfile = "NBX_perFill_2015.csv"

allGood = []
wbmTargetBad = []
wbmCollidingBad = []
otherBad = []

with open(infile) as inputFile:
    outputFile = open(outfile, "w")

    reader = csv.reader(inputFile, delimiter=",")
    for row in reader:
        
        # Skip any rows which don't contain a comma (these should just be warning messages)
        if len(row) == 1:
            continue

        # Fields are: fill number, WBM target, WBM colliding, beam, luminometers
        if (row[1] == row[2] and row[2] == row[3] and row[3] == row[4]):
            allGood.append(row[0])
        elif (row[2] == row[3] and row[3] == row[4]):
            wbmTargetBad.append(row[0])
        elif (row[1] == row[3] and row[3] == row[4]):
            wbmCollidingBad.append(row[0])
        else:
            otherBad.append(",".join(row))
            
        outputFile.write(row[0]+","+row[4]+"\n")

    outputFile.close()

print "All good:"
print ", ".join(allGood)
print "WBM target bad:"
print ", ".join(wbmTargetBad)
print "WBM colliding bad:"
print ", ".join(wbmCollidingBad)
if otherBad:
    print "More substantial disagreements:"
    print "\n".join(otherBad)

print "Wrote output to", outfile

