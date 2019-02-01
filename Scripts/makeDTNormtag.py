#!/usr/bin/env python

# This script makes the 2018 DT normtag. This is necessary because the DT normtag includes a constant factor
# for background subtraction but the way this is implemented in brilcalc means that it needs to be divided by
# the number of bunches in order to come out correctly.

import csv

fill_info_file = "/afs/cern.ch/user/p/plujan/FillInformation/Run2FillData.csv"
start_fill = 6570

sigmavis = 182981
background = 210

orbit_freq = 1/(3564*24.95e-9)
a1 = orbit_freq/sigmavis
a0 = -a1*background

last_nbx = -1

with open(fill_info_file) as fill_info:
    reader = csv.reader(fill_info, delimiter=',')
    for row in reader:
        if row[1] == "nbx":
            continue

        fill = int(row[0])
        if fill < start_fill:
            continue

        nbx = int(row[1])
        start_run = int(row[4])

        if (nbx != last_nbx):
            print "    - %d:" % (start_run)
            print "        func: poly1d"
            print "        payload: {'coefs': '%.5f, %.5f'}" % (a1, a0/nbx)
            print "        comments: sigmavis %d, background %d, nbx %d" % (sigmavis, background, nbx)
        last_nbx = nbx
