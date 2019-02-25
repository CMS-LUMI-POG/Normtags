#!/usr/bin/env python
#
# Given a composite normtag file, this will print out what fraction of the file (by lumisection) comes from
# each of the individual detectors.

import os, sys, argparse, json

parser = argparse.ArgumentParser()
parser.add_argument("normtag_file", help="Input normtag file")
args = parser.parse_args()

with open(args.normtag_file) as normtag_input:
    parsed_normtag = json.load(normtag_input)

normtag_ls = {}
try:
    for entry in parsed_normtag:
        l = entry[0]
        if l not in normtag_ls:
            normtag_ls[l] = 0
        runs = entry[1].keys()
        assert(len(runs) == 1)
        run = runs[0]
        # Count the number of lumisections in each range specified and add them to the total.
        for run_range in entry[1][run]:
            normtag_ls[l] += run_range[1] - run_range[0] + 1

except:
    print "Something went wrong in parsing the input normtag file. Please check the file."
    sys.exit(1)

tot_ls = 0
for l in normtag_ls:
    tot_ls += normtag_ls[l]

for l in normtag_ls:
    print "%s: %d/%d (%.2f%%)" % (l, normtag_ls[l], tot_ls, 100.0*normtag_ls[l]/tot_ls)
