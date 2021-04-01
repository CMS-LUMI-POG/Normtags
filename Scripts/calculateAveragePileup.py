#!/usr/bin/env python

# This is a simple script that will take the output of brilcalc --byls (but not with --xing) and calculate the
# average pileup over the input file.
#
# It will provide two different computations:

# 1) The simple average over all lumisections, which is appropriate if you're interested in the average pileup
# *delivered*.
#
# 2) The average weighted by recorded lumi, which is appropriate if you're interested in the average pileup
# *in your dataset*. (Why the difference? Because the amount of data taken by a given trigger is also
# generally proportional to the pileup, so that's why the additional weight.)

import sys, csv, argparse

parser = argparse.ArgumentParser()
parser.add_argument("input_file", help="Input csv file")
args = parser.parse_args()

nrows = 0
sumpu = 0
totrec = 0
sumpu_weight = 0
with open(args.input_file) as csv_input:
    reader = csv.reader(csv_input, delimiter=",")
    for row in reader:
        if row[0][0] == '#':
            continue

        reclumi = float(row[6])
        pu = float(row[7])

        nrows += 1
        sumpu += pu
        totrec += reclumi
        sumpu_weight += pu*reclumi

print "Simple average PU over %d LS is %.2f" % (nrows, sumpu/nrows)
print "Average PU weighted by recorded luminosity is %.2f" % (sumpu_weight/totrec)
