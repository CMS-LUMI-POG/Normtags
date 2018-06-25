#!/usr/bin/env python

# This script takes a CSV input file with data intended for loading into the lumiDB and performs some
# validation to make sure that the data is OK.

import csv
import sys
import os
import numpy

# This assumes that the input format is something like
# run, LS, total lumi, bx lumi. If there's more header fields (fill or whatever),
# adjust this appropriately.
numHeaderFields = 2

# How closely we need the per-BX luminosity sum to match the total luminosity. For PCC, these tend
# to match not very well when the overall luminosity is low, so we establish a looser threshold
# for those.
sumPrecision = 0.01      # normally we require agreement within 1%
lowLumiThreshold = 2000  # but if the luminosity is lower than this value...
sumPrecisionLow = 0.06   # then only require agreement within 6%

nBX = 3564

# Counters.
numGoodLines = 0
numWarningLines = 0
numErrorLines = 0

if (len(sys.argv) < 2):
    print "Usage: validateInputFile.py [file]"
    sys.exit(1)

with open(sys.argv[1]) as inputFile:
    reader = csv.reader(inputFile, delimiter=',')
    for row in reader:
        if row[0][0] == '#':
            continue

        if len(row) != numHeaderFields + 1 + nBX:
            print "Error: number of fields not what we were expecting in",":".join(row[0:numHeaderFields])
            #sys.exit(1)
            numErrorLines += 1
            continue
            
        # Check two things: 1) that there are no NaN or Inf values, 2) that the per-BX luminosities are (more or less)
        # consistent with the total luminosity
        totalLum = float(row[numHeaderFields])

        if (numpy.isinf(totalLum) or numpy.isnan(totalLum)):
            print "Error: total luminosity is nan or inf in",":".join(row[0:numHeaderFields])
            numErrorLines += 1
            continue

        bxSumLum = 0
        badBX = False
        for bx in range(3564):
            thisLum = float(row[numHeaderFields+1+bx])
            if (numpy.isinf(thisLum) or numpy.isnan(thisLum)):
                print "Error: luminosity for BX",bx,"is nan or inf in",":".join(row[0:numHeaderFields])
                # don't drop out just yet since if there are other bad BXes in this line we should flag them too
                badBX = True
            bxSumLum += float(row[numHeaderFields+1+bx])

        if badBX:
            numErrorLines += 1
            continue

        targetPrecision = sumPrecision
        if (totalLum < lowLumiThreshold):
            targetPrecision = sumPrecisionLow

        if totalLum < bxSumLum*(1-targetPrecision) or totalLum > bxSumLum*(1+targetPrecision):
            print "Warning: total lumi is",totalLum,"but sum of BX lumi is",bxSumLum,"in",":".join(row[0:numHeaderFields])
            numWarningLines += 1
        else:
            #print "Lumi matches within precision (total is",totalLum,")"
            numGoodLines += 1

print "Total of",numGoodLines+numWarningLines+numErrorLines,"records processed"
print numGoodLines,"records validated successfully"
print numWarningLines,"records with warnings"
print numErrorLines,"records with errors"


