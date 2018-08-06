#!/usr/bin/env python

# intersectJSONNormtag.py
#
# This script takes an input JSON file (first argument) and a normtag file (second argument) and produces an
# output JSON file which is the intersection of the two. You can run this repeatedly to get the intersection
# of multiple normtag files as well.

import os, sys, argparse, json

parser = argparse.ArgumentParser()
parser.add_argument("jsonFile", help="Input JSON file")
parser.add_argument("normtagFile", help="Input normtag file")
args = parser.parse_args()

# First, read in the input JSON file.
with open(args.jsonFile) as json_input:
    parsedJSON = json.load(json_input)
# Convert this into a dictionary of sets, so we can more easily delete things from it.
json_ls = {}
try:
    for run in parsedJSON:
        json_ls[run] = set()
        for runRange in parsedJSON[run]:
            for ls in range(runRange[0], runRange[1]+1):
                json_ls[run].add(ls)
except:
    print "Something went wrong in parsing the input JSON file. Please check the format, and make sure that"
    print "you specified the JSON file first and the normtag file second."
    sys.exit(0)

# Same deal with the normtag file. A little more complicated since the normtag file has a more complicated
# format.
with open(args.normtagFile) as normtag_input:
    parsedNormtag = json.load(normtag_input)

normtag_ls = {}
try:
    for entry in parsedNormtag:
        runs = entry[1].keys()
        assert(len(runs) == 1)
        run = runs[0]
        if not run in normtag_ls:
            normtag_ls[run] = set()
        for runRange in entry[1][run]:
            for ls in range(runRange[0], runRange[1]+1):
                normtag_ls[run].add(ls)
except:
    print "Something went wrong in parsing the input normtag file. Please check the format, and make sure that"
    print "you specified the JSON file first and the normtag file second."
    sys.exit(0)


# Now add all of the lumisections which appear in both to the output.

output_ls = {}
for run in json_ls:
    for ls in json_ls[run]:
        if (run in normtag_ls) and (ls in normtag_ls[run]):
            if run in output_ls:
                output_ls[run].add(ls)
            else:
                output_ls[run] = set([ls])

# Finally, convert this back into an array of ranges. This code stolen from select_low_pileup.py because it
# works (maybe someday there'll actually be a standardized library we can use for that).

lastRun = -1
startLS = -1
lastLS = -1
output_json = {}

def add_to_list(run, startLS, lastLS):
    if not run in output_json:
        output_json[run] = [[startLS, lastLS]]
    else:
        output_json[run].append([startLS, lastLS])
    
for r in sorted(output_ls.keys()):
    for ls in sorted(output_ls[r]):
        # If new run, or discontinuous LS range, save the previous range and move on
        if ((r != lastRun and lastRun != -1) or
            (ls != lastLS + 1 and lastLS != -1)):
            add_to_list(str(lastRun), startLS, lastLS)
            startLS = ls
        lastRun = r
        lastLS = ls
        if startLS == -1:
            startLS = ls
# Don't forget the end! However if we got nothing at all, then do forget the end.
if (lastRun != -1):
    add_to_list(str(lastRun), startLS, lastLS)

# Unfortunately json.dump only has two kinds of formatting: either everything on one line,
# or else every single list element on its own line, both of which are rather difficult to
# read. So instead iterate over the dictionary ourselves and use json.dumps to format each
# element. Not the most elegant solution in the world, but it works.
output_lines = []
for r in sorted(output_json.keys()):
    output_lines.append("\""+r+"\": "+json.dumps(output_json[r]))
print("{")
print(",\n".join(output_lines))
print("}")
