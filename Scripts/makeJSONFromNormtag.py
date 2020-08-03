#!/usr/bin/python

# This script will take a normtag file and produce a JSON file containing the list of lumisections covered by
# that normtag, so you can use it in, for example, the -i input to brilcalc.

import json
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("normtag_file", help="Input normtag file")
parser.add_argument("json_file", help="Output JSON file")
args = parser.parse_args()

with open(args.normtag_file) as normtag_input:
    parsed_normtag = json.load(normtag_input)

output_lumisections = {}

for i in parsed_normtag:
    if len(i[1].keys()) != 1:
        print "Error: malformed entry", i
        sys.exit(1)
    run = i[1].keys()[0]
    lumis = i[1][run]
    
    for lsrange in lumis:
        if len(lsrange) != 2:
            print "Error: malformed entry", i
            sys.exit(1)
        if lsrange[1] < lsrange[0]:
            print "Error: malformed entry",i
        # if this run isn't yet in the output, add it there
        if run not in output_lumisections:
            output_lumisections[run] = [lsrange]
        # if this run is in the output, and this lumisection range is contiguous with the last one,
        # then extend it
        elif output_lumisections[run][-1][1] == lsrange[0] - 1:
            output_lumisections[run][-1][1] = lsrange[1]
        # otherwise, add it as a new entry
        else:
            output_lumisections[run].append(lsrange)

# json.dump(output_lumisections, sys.stdout, sort_keys=True)

with open(args.json_file, "w") as json_output:
    json.dump(output_lumisections, json_output, sort_keys=True)
print "Output written to "+args.json_file+"."
