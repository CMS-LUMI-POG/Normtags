#!/usr/bin/python

import os, sys, csv

# This script is a companion to getNBX.py. If you run it and see that there's a discrepancy between the beam
# data and the luminometer data, run this script to do some more detailed investigation.

# Threshold in the beam data to count a bunch as filled
beamIntensityThreshold = 2e9

luminometerList = ["hfet", "pltzero"] # for 2017-18; use hfoc instead of hfet for 2016

if len(sys.argv) < 2:
    print "Usage: "+sys.argv[0]+" [fills]"
    sys.exit(0)

fillList = [int(a) for a in sys.argv[1:]]

for fill in fillList:

    # First get the pattern from the luminometers. We assume that you've already investigated and resolved any
    # differences between the individual luminometers, so just grab the first pattern and move on.

    nBunchLumi = -1

    filledBunchesLumi = set()

    # We should still loop over luminometers in case the first luminometer doesn't have any data for some
    # reason.
    for luminometer in luminometerList:
        dataFileName = "bxdata_"+str(fill)+"_"+luminometer+".csv"
        
        with open(dataFileName) as dataFile:
            reader = csv.reader(dataFile, delimiter=',')
            for row in reader:
                if row[0][0] == '#':
                    continue

                # Split up the individual BX data. Use the slice to drop the initial and final brackets.
                if (row[9][0:2] == '[]'):
                    bxFields = []
                else:
                    bxFields = row[9][1:-1].split(' ')

                # Get the list of filled bunches.
                for i in range(0, len(bxFields), 3):
                    filledBunchesLumi.add(int(bxFields[i]))

                nBunchLumi = len(filledBunchesLumi)
                
                # Now we successfully have the data, no point to keep going through the file at this point
                break
            # end of loop over rows
        # end of file read
    
        # If we successfully got data from this luminometer, don't bother with the other one(s). Otherwise
        # keep going.
        if (nBunchLumi != -1):
            break
    # end of loop over luminometers
    print "Found",nBunchLumi,"bunches from luminometer data"

    # Next let's take a look at the per-BX beam data and investigate any disagreements. Unlike above, let's go
    # through the whole file just to make sure there aren't any discrepancies within the file.

    beamFileName = "bxdata_"+str(fill)+"_beam.csv"
    if not os.path.exists(beamFileName):
        os.system("brilcalc beam --xing -f "+str(fill)+" -o "+beamFileName)
    
    filledBunchesBeam = set()
    nBunchBeam = -1

    with open(beamFileName) as beamFile:
        reader = csv.reader(beamFile, delimiter=',')
        for row in reader:
            if row[0][0] == '#':
                continue

            # Split up the individual BX data. Use the slice to drop the initial and final brackets.
            if (row[4][0:2] == '[]'):
                bxFields = []
            else:
                bxFields = row[4][1:-1].split(' ')

            # Get the list of filled bunches. Note: for these purposes, we only care if both beam 1 and beam 2
            # are filled over the threshold above.
            thisFilledBunches = set()
            for i in range(0, len(bxFields), 3):
                if (float(bxFields[i+1]) > beamIntensityThreshold and float(bxFields[i+2]) > beamIntensityThreshold):
                    thisFilledBunches.add(int(bxFields[i]))

            if (nBunchBeam == -1):
                nBunchBeam = len(thisFilledBunches)
                filledBunchesBeam = thisFilledBunches
            # Note: sometimes you'll have beam data after beam dump so we can cheerfully ignore those.
            elif (nBunchBeam != len(thisFilledBunches)) and len(thisFilledBunches) != 0:
                print "Warning: mismatch in number of colliding bunches in "+row[1]+":"+row[2]+" -- expected",nBunchBeam,"got",len(thisFilledBunches)
                if len(thisFilledBunches - filledBunchesBeam) > 0:
                    print "Extra bunches:",sorted(thisFilledBunches - filledBunchesBeam)
                if len(filledBunchesBeam - thisFilledBunches) > 0:
                    print "Missing bunches:",sorted(filledBunchesBeam - thisFilledBunches)

    if (nBunchBeam == -1):
        print "Error: failed to find number of bunches in beam data for fill",fill
    else:
        print "Found",nBunchBeam,"colliding bunches in beam data for fill",fill
        if (filledBunchesBeam != filledBunchesLumi):
            extraBunchesBeam = filledBunchesBeam - filledBunchesLumi
            extraBunchesLumi = filledBunchesLumi - filledBunchesBeam
            if len(extraBunchesBeam) > 0:
                print "Bunches in beam but not in lumi:",sorted(extraBunchesBeam)
            if len(extraBunchesLumi) > 0:
                print "Bunches in lumi but not in beam:",sorted(extraBunchesLumi)
