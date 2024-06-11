#!/usr/bin/env python3

import sys
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--normtaglist", help="Comma-separated list of normtags (e.g. 'nt1.json,nt2.json')")
parser.add_argument("-o", "--outputfiles", nargs=2, default=("compositeNT_first.json", "compositeNT_second.json"), help="two output file names")
parser.add_argument("--minrun", default=0, type=int, help="minimum run number to consider (default: 0)")
parser.add_argument("--maxrun", default=1e7, type=int, help="maximum run number to consider (default: 1e7)")
parser.add_argument("-q", "--quiet", action="store_true", help="don't print warning about missing iovtags")
args = parser.parse_args()

normtagslist = args.normtaglist.split(",")
print(normtagslist)

normtags={}
for normtagfilename in normtagslist:
    with open(normtagfilename) as f:
        normtags[normtagfilename] = json.load(f)

firstiovtags = {}
secondiovtags = {}

# identify which iovtag to use for which run/lumisection
for normtagfilename in normtagslist:
    for line in normtags[normtagfilename]:
        iovtag = line[0]
        for runstr, lsranges in line[1].items():
            run = int(runstr)
            if run < args.minrun or run > args.maxrun:
                continue
            if run not in firstiovtags:
                firstiovtags[run] = {}
                secondiovtags[run] = {}
            for lsrange in lsranges:
                for ls in range(lsrange[0], lsrange[1]+1):
                    if ls not in firstiovtags[run]:
                        firstiovtags[run][ls] = iovtag
                    elif ls not in secondiovtags[run]:
                        secondiovtags[run][ls] = iovtag

# check if any run/lumisection has a first but no second iovtag
if not args.quiet:
    missing = {}
    for run in firstiovtags.keys():
        for ls in firstiovtags[run].keys():
            if ls not in secondiovtags[run].keys():
                if run not in missing:
                    missing[run] = []
                missing[run].append(ls)
        if run in missing.keys():
            print("WARNING: Did not find two available iovtags for run {}: lumisections {}".format(run, ', '.join(map(str, missing[run]))))

# check for any empty runs
todelete = []
for run in firstiovtags.keys():
    if not firstiovtags[run]:
        todelete.append(run)
for run in todelete:
    del firstiovtags[run]
    del secondiovtags[run]

# construct content of new composite normtag files
def makeNTfrom(iovtags):
    NT = []
    for run in sorted(iovtags.keys()):
        content = []
        for ls in sorted(iovtags[run].keys()):
            if content and content[-1][1]==ls-1 and content[-1][2]==iovtags[run][ls]:
                content[-1][1] = ls
            else:
                content.append([ls, ls, iovtags[run][ls]])
        for firstls, lastls, iovtag in content:
            NT.append([iovtag, run, firstls, lastls])
    return NT
firstNT = makeNTfrom(firstiovtags)
secondNT = makeNTfrom(secondiovtags)

def writeNTtofile(outputfilename, NT):
    with open(outputfilename, "w") as f:
        f.write("[\n")
        f.write(",\n".join(map(lambda content: "[\"{0}\", {{\"{1}\": [[{2}, {3}]]}}]".format(*content), NT)))
        f.write("\n]\n")
writeNTtofile(args.outputfiles[0], firstNT)
writeNTtofile(args.outputfiles[1], secondNT)
