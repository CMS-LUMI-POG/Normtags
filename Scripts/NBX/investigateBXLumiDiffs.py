#!/usr/bin/python

import os, sys, csv

# This script is a companion to getNBX.py which will further investigate in detail discrepancies in the
# per-luminometer bunch data. Run it with one or more fills as arguments and it'll give you some more
# information about why exactly the luminometers differ.

luminometerList = ["hfoc", "pltzero"]

if len(sys.argv) < 1:
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
                if linenum > 25:
                    break

                # Next, split up the individual BX data. Use the slice
                # to drop the initial and final brackets.
                thisNBunch = 0
                if (row[9][0:2] == '[]'):
                    bxFields = []
                else:
                    bxFields = row[9][1:-1].split(' ')
                avgLumi = 0

                # Get the list of filled bunches.
                thisFilledBunches = set()
                for i in range(0, len(bxFields), 3):
                    thisFilledBunches.add(int(bxFields[i]))

                if (nBunchLumi == -1):
                    nBunchLumi = len(thisFilledBunches)
                    filledBunchesRef = thisFilledBunches
                # Otherwise, see if we match.
                else:
                    if (nBunchLumi != len(thisFilledBunches)):
                        # There's a difference. Figure out what it is.
                        extraBunches = thisFilledBunches - filledBunchesRef
                        missingBunches = filledBunchesRef - thisFilledBunches
                        print "Mismatch in numBX "+luminometer+" run:fill "+row[0]+" ls "+row[1]+": expected",nBunchLumi,"got",len(thisFilledBunches)
                        if len(missingBunches) > 0:
                            print "Bunches missing:",sorted(missingBunches)
                        if len(extraBunches) > 0:
                            print "Extra bunches:",sorted(extraBunches)

            # end of loop over rows
        # end of file read
    
    # end of loop over luminometers
    # print "Found",nBunchLumi,"bunches from luminometer data"
