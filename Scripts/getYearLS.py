#!/usr/bin/env python

import os, sys
import argparse
import csv
import json

# This script creates a JSON file containing a list of all lumisections (13 TeV, pp, STABLE BEAMS only) for
# which we have lumi data. It gets this data by doing a query of the form
# brilcalc lumi --byls --begin '01/01/18 00:00:00' --end '12/31/18 23:59:59' -b "STABLE BEAMS"
# and then again with a normtag. It will then compare the results with the DCSOnly json and see if there is
# anything missing. Note that this CANNOT detect any lumisections which are lacking luminosity data and are
# not in the 13TeV DCSOnly json, so don't think that this is perfect!
#
# Note: if there are any lumisections where delivered == recorded == 0, these will be dropped. Note that I
# normally expect these to happen at the end of a fill, when the fill has actually ended but there are still a
# few lumisections before the STABLE BEAMS flag is cleared, but if these are not at the end of a fill a
# warning will be raised.
#
# Arguments:
# -y, --year (required): two-digit year number to generate for
# -o, --outfile (optional): output file name, defaults to output.json
# -n, --normtag (optional): normtag to use; if not specified, will be
# /cvmfs/cms-bril.cern.ch/cms-lumi-pog/Normtags/normtag_PHYSICS.json
# -j, --jsonfile (optional): JSON file to compare with; if not specified, will default to
# /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions${YEAR}/13TeV/DCSOnly/json_DCSONLY.txt

default_normtag = "/cvmfs/cms-bril.cern.ch/cms-lumi-pog/Normtags/normtag_PHYSICS.json"
default_jsonfile = "/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions%d/13TeV/DCSOnly/json_DCSONLY.txt"

temp_name_online = "temp_online.csv"
temp_name_normtag = "temp_normtag.csv"

parser = argparse.ArgumentParser()
parser.add_argument('-y', '--year', type=int, required=True, help='Year (in two-digit format) to generate JSON file for.')
parser.add_argument('-o', '--outfile', help='Output file name', default='output.json')
parser.add_argument('-n', '--normtag', help='Normtag to use. Will default to normtag_PHYSICS if not specified.', default=default_normtag)
parser.add_argument('-j', '--jsonfile', help='JSON file to compare against. Will default to DCSOnly JSON if not specified.')
args = parser.parse_args()

year = args.year
if len(str(year)) != 2:
    print "Error: please specify the year as a two-digit number (e.g., 18)"
    sys.exit(1)

if args.jsonfile:
    jsonfile = args.jsonfile
else:
    jsonfile = default_jsonfile % (year)
normtag = args.normtag

def get_lumisections(file_name):
    parsed_data = {}
    dropped_last = False
    dropped_fill = -1
    with open(file_name) as csvFile:
        reader = csv.reader(csvFile, delimiter=",")
        for row in reader:
            if row[0][0] == '#':
                continue
            runfill = row[0].split(":")
            lsls = row[1].split(":")
            run = int(runfill[0])
            fill = int(runfill[1])
            ls = int(lsls[0])
            # Check to see if this was zero and if so drop it.
            if float(row[5]) == 0.0 and float(row[6]) == 0.0:
                dropped_last = True
                dropped_fill = fill
                continue
            # If not, make sure that we've started a new fill. Otherwise something has gone wrong!
            if dropped_last == True and fill == dropped_fill:
                print "Got lumisections after lumisections with zero luminosity but not in a different fill! At fill",fill,"run",run,"ls",ls
            dropped_last = False
            if run not in parsed_data:
                parsed_data[run] = set()
            parsed_data[run].add(ls)
    return parsed_data

def format_range(first, last):
    if (first == last):
        return str(first)
    else:
        return ("%d-%d" % (first, last))

# requires items to be non-empty
def format_items_as_range(items):
    total = ""
    sorted_items = sorted(items)
    first_in_range = sorted_items[0]
    last_item = sorted_items[0]
    for i in sorted_items[1:]:
        if last_item+1 != i:
            total += format_range(first_in_range, last_item) + " "
            first_in_range = i
        last_item = i
    total += format_range(first_in_range, last_item)
    return total

print "Getting full year data with no normtag, this will take a few moments..."
os.system("brilcalc lumi --byls --begin \'01/01/%d 00:00:00\' --end \'12/31/%d 23:59:59\' -b \"STABLE BEAMS\" -o %s" % (year, year, temp_name_online))
parsed_data_online = get_lumisections(temp_name_online)

print "Getting full year data with normtag, this will also take a few moments..."
os.system("brilcalc lumi --byls --begin \'01/01/%d 00:00:00\' --end \'12/31/%d 23:59:59\' -b \"STABLE BEAMS\" --normtag %s -o %s" % (year, year, normtag, temp_name_normtag))
parsed_data_normtag = get_lumisections(temp_name_normtag)

print "Getting data from JSON file, this will be real fast..."
parsed_data_json = {}
with open(jsonfile) as json_input:
    parsed_json = json.load(json_input)
for r in parsed_json:
    run = int(r)
    parsed_data_json[run] = set()
    for run_range in parsed_json[r]:
        for ls in range(run_range[0], run_range[1]+1):
            parsed_data_json[run].add(ls)

# This function finds things in set1 but not set2.
def find_missing_elements(set1, set2):
    diff = False
    for r in sorted(set1.keys()):
        if r not in set2:
            print "all of run",r
            diff = True
        elif len(set1[r] - set2[r]) > 0:
            print "Run", r, "lumisections:", format_items_as_range(set1[r] - set2[r])
            diff = True
    if diff == False:
        print "none"
        
print "Lumisections in online but not normtag:"
find_missing_elements(parsed_data_online, parsed_data_normtag)
print "Lumisections in normtag but not online:"
find_missing_elements(parsed_data_normtag, parsed_data_online)

# Merge online and normtag together.
all_lumi_ls = {}
all_runs = set(parsed_data_online.keys()) | set(parsed_data_normtag.keys())
for r in sorted(all_runs):
    all_lumi_ls[r] = set()
    if r in parsed_data_online:
        all_lumi_ls[r] |= parsed_data_online[r]
    if r in parsed_data_normtag:
        all_lumi_ls[r] |= parsed_data_normtag[r]

# Check for differences with json.
print "Lumisections in JSON but not luminometer data:"
find_missing_elements(parsed_data_json, all_lumi_ls)
# Note -- it is of course normal for the JSON to be a subset of the luminometer data, so no point in doing the
# reverse comparison.

# Now prepare for output. First we need to convert to an array of ranges. Almost the same as format_items_as_range above.
output_dict = {}
for r in sorted(all_lumi_ls):
    output_dict[r] = []

    sorted_items = sorted(all_lumi_ls[r])
    first_in_range = sorted_items[0]
    last_item = sorted_items[0]
    for i in sorted_items[1:]:
        if last_item+1 != i:
            output_dict[r].append([first_in_range, last_item])
            first_in_range = i
        last_item = i
    output_dict[r].append([first_in_range, last_item])

os.unlink(temp_name_online)
os.unlink(temp_name_normtag)

with open(args.outfile, "w") as outfile:
    json.dump(output_dict, outfile)
print "Output JSON file written to", args.outfile
