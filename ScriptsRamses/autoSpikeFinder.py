#!/usr/bin/env python

# This is a first attempt at automatically detecting spikes in the brilcalc data for a given luminometer. To
# use it, just produce the brilcalc output as normal, and then invoke this script on the output.
#
# The algorithm used is pretty crude: it keeps a running average of the last 10 LS, not counting the one
# immediately preceding the current one, and if that average is pretty stable (to exclude times when the
# luminosity is changing significantly, like an emittance scan or a change in crossing angle) and the current
# LS is significantly higher than that average, it will flag that LS as potentially bad.
#
# The algorithm will miss spikes in several cases:
# a) spikes actually during an emittance scan, or immediately after an emittance scan/crossing angle
# change/other true change in luminosity
# b) if there are multiple spikes in close proximity, only the first will be found
# c) spikes within the first 10 LS of the fill will be missed
#
# so this should not be treated as anything close to the final word! In fact, I only made this script to check
# the results of the (even more crude) automatic spike finder I implemented for the validation of the 2018
# RAMSES data. However, I've left it here in case anyone is interested in doing further investigations.
#
# In general, I think trying to find spikes from the single luminometer data alone is unlikely to be entirely
# successful -- I think you'll always end up needing to do a fair amount of manual work. Probably you'll need
# a reference luminometer that you can compare against (although of course then you have the possibilities of
# data issues in the other luminometer).

# Paul Lujan, 2/28/19

import argparse, csv
from collections import deque

parser = argparse.ArgumentParser()
parser.add_argument("csvFile", help="brilcalc output file")
args = parser.parse_args()

# First, read in the input JSON file.
lastFill = -1

# This list tracks the last 11 lumisections. It's a deque so we can pop the oldest one off the left and push
# the newest one onto the right.
last_lumis = deque(maxlen=11)
with open(args.csvFile) as csv_input:
    reader = csv.reader(csv_input, delimiter=',')
    for row in reader:
        if row[0][0] == '#':
            continue
        runfill = row[0].split(':')
        run = int(runfill[0])
        fill = int(runfill[1])
        lsnums = row[1].split(':')
        ls = int(lsnums[0])
        lumi_del = float(row[5])
        
        # Reset last list if we're starting a new fill.
        if fill != lastFill:
            last_lumis.clear()
        lastFill = fill

        # Compute average of 10 LSes NOT including the most recent one
        # (because that one might also be a spike).
        if len(last_lumis) == 11:
            tot_lum = last_lumis[0]
            max_lum = last_lumis[0]
            min_lum = last_lumis[0]
            for i in range(1,10):
                tot_lum += last_lumis[i]
                if last_lumis[i] > max_lum:
                    max_lum = last_lumis[i]
                if last_lumis[i] < min_lum:
                    min_lum = last_lumis[i]
            avg = tot_lum/10
            # If the average is stable, then look to see if we're not within it.
            if max_lum/avg < 1.05 and min_lum/avg > 0.95:
                if lumi_del - avg > 1000:
                    # Looks like a spike!
                    print fill,str(run)+":"+str(ls)
            #print fill, "avg=",avg,"max=",max_lum,"min=",min_lum

        # Add this lumi to the deque and continue on.
        last_lumis.append(lumi_del)
            
