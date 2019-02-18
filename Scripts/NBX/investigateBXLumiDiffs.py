#!/usr/bin/python

import os, sys, csv

# This script is a companion to getNBX.py which will further investigate in detail discrepancies in the
# per-luminometer bunch data. Run it with one or more fills as arguments and it'll give you some more
# information about why exactly the luminometers differ.

luminometerList = ["hfet", "pltzero"]  # for 2017-18; use hfoc instead of hfet for 2015-16

# If we see a difference between the two patterns, we can try shifting the second so it matches the first.
# This is pretty slow so turn this on only if you want to use it.
findShift = False

# If there's a known shift for one or more luminometers, you can apply it here so that it's already accounted
# for. Note that the value here is the correction to be applied (e.g. for the early 2017 HFET fills, the HFET
# data was shifted by -1 BX relative to correct, so you needed to apply a shift of +1 to recover the correct
# values). All of the 2017 data has now been corrected so you don't need these here any more!

knownShifts = {"hfet": {}, "pltzero": {}}

#               "hfet": {"5698": 1, "5699": 1, "5704": 1, "5710": 1, "5717": 1,
#                        "5718": 1, "5719": 1, "5722": 1, "5730": 1, "5737": 1,
#                        "5746": 1, "5749": 1, "5750": 1, "5822": 1, "5824": 1,
#                        "5825": 1, "5830": 1, "5833": 1, "5834": 1},
#               "pltzero": {"5883": 2071, "6364": 188}


if len(sys.argv) < 2:
    print "Usage: "+sys.argv[0]+" [fills]"
    sys.exit(0)

fillList = [int(a) for a in sys.argv[1:]]

# The parsing code is the same as in getNBX.py but we also keep track of the whole pattern so we can look for
# differences in more detail.

for fill in fillList:
    # Check the colliding bunch data and look for differences.

    nBunchLumi = -1

    filledBunchesRef = set()

    for luminometer in luminometerList:
        dataFileName = "bxdata_"+str(fill)+"_"+luminometer+".csv"

        applyShift = 0
        if luminometer in knownShifts and str(fill) in knownShifts[luminometer]:
            applyShift = knownShifts[luminometer][str(fill)]
            print "Note: shifting data for",luminometer,"by",applyShift,"BX"
        
        with open(dataFileName) as dataFile:
            reader = csv.reader(dataFile, delimiter=',')
            for linenum, row in enumerate(reader):
                if row[0][0] == '#':
                    continue

                # To save time and annoyance, just consider the first 25 lines of the file, since presumably
                # any differences in the rest of the file are due to either (a) specific luminometer issues
                # (which we don't really care about for this purpose) or (b) a bunch decaying faster than its
                # companions (which can happen but we can't really account for that in our simple total so
                # let's not worry about it).

                # Note: if you're investigating shifts you should comment this out since often those start at
                # a particular time mid-fill.

                if linenum > 25:
                    break

                # Next, split up the individual BX data. Use the slice to drop the initial and final brackets.
                thisNBunch = 0
                if (row[9][0:2] == '[]'):
                    bxFields = []
                else:
                    bxFields = row[9][1:-1].split(' ')
                avgLumi = 0

                # Get the list of filled bunches.
                thisFilledBunches = set()
                for i in range(0, len(bxFields), 3):
                    thisBX = int(bxFields[i])
                    thisBX += applyShift
                    if thisBX > 3564:
                        thisBX -= 3564
                    thisFilledBunches.add(thisBX)

                # Store this if this is the first (non-empty) pattern we've seen.
                if (nBunchLumi == -1 and len(thisFilledBunches) > 0):
                    nBunchLumi = len(thisFilledBunches)
                    filledBunchesRef = thisFilledBunches
                # Otherwise, see if we match.
                else:
                    if (thisFilledBunches != filledBunchesRef):
                        # There's a difference. Figure out what it is.
                        extraBunches = thisFilledBunches - filledBunchesRef
                        missingBunches = filledBunchesRef - thisFilledBunches
                        if nBunchLumi != len(thisFilledBunches):
                            print "Mismatch in numBX "+luminometer+" run:fill "+row[0]+" ls "+row[1]+": expected",nBunchLumi,"got",len(thisFilledBunches)
                        else:
                            print "Bunches are shifted in "+luminometer+" run:fill "+row[0]+" ls "+row[1]
                        if len(missingBunches) > 0:
                            print "Bunches missing:",sorted(missingBunches)
                        if len(extraBunches) > 0:
                            print "Extra bunches:",sorted(extraBunches)
                        if findShift:
                            for tryShift in range(1,3564):
                                newBunchSet = set()
                                for bx in thisFilledBunches:
                                    newBunch = bx + tryShift
                                    if newBunch > 3564:
                                        newBunch -= 3564
                                    newBunchSet.add(newBunch)
                                sumDiff = len(filledBunchesRef-newBunchSet) + len(newBunchSet-filledBunchesRef)
                                if sumDiff < 25:
                                    print "Reasonably good match with shift",tryShift,"mismatch is",sumDiff
                    # else:
                    #     print "Match for "+luminometer+" run:fill "+row[0]+" ls "+row[1]
            # end of loop over rows
        # end of file read
    
    # end of loop over luminometers
    print "Found",nBunchLumi,"bunches from luminometer data"
