#!/usr/bin/env python

# makeValidationSummary.py
#
# This script makes a plot summarizing the overall results of the fill validation script. Just put in the
# luminometers, runs, etc.  to use below and run.

import os, sys, json
import matplotlib.pyplot as plt

# Luminometers to make the plot for. Recommended to include only one of HFOC/HFET since normally they're
# invalidated together anyway.

luminometers = ["hfet", "pltzero", "bcm1f", "dt"]

# Run range to consider. Use -1 to specify all runs.
first_run = 314472 # beginning of 2018
last_run = -1

normtag_file_form = "../normtag_%s.json"
output_file_name = "validationPerformance.png"

# Read in all the individual normtag files.
valid_lumisections = {}
for l in luminometers:
    valid_lumisections[l] = set()
    
    normtag_file_name = normtag_file_form % (l)
    print "Reading normtag file "+normtag_file_name+"..."
    with open(normtag_file_name) as normtag_input:
        parsed_normtag = json.load(normtag_input)

    # For each normtag, just dump the valid lumisections into a giant set.

    try:
        for entry in parsed_normtag:
            runs = entry[1].keys()
            assert(len(runs) == 1)
            run = runs[0]
            if (first_run != -1 and int(run) < first_run):
                continue
            if (last_run != -1 and int(run) > last_run):
                continue
            for run_range in entry[1][run]:
                for ls in range(run_range[0], run_range[1]+1):
                    valid_lumisections[l].add(run+":"+str(ls))
    except:
        print "Something went wrong in parsing the "+l+" normtag file. Please check the file format."
        sys.exit(0)

# To determine all lumisections, just take the intersection of all individual luminometers. This may be not
# quite right if there's a lumisection missing from all luminometers, but (a) I don't think that's the case
# for 2018, and (b) even if so it's an extremely small set.

valid_lumisections_all = set()
for l in luminometers:
    valid_lumisections_all.update(valid_lumisections[l])
tot_lumisections = len(valid_lumisections_all)
print "Total of",tot_lumisections,"lumisections read."

# Sort the lumisections into N+3 categories:
# 1) lumisections valid for all luminometers
# 2...N+1) lumisections valid for all but one specific luminometer
# N+2) lumisections invalid for two luminometers
# N+3) lumisections invalid for three or more luminometers

lumisections_count = [0]*(len(luminometers)+3)

lumisections_missing = {}
for l in luminometers:
    lumisections_missing[l] = 0

for s in valid_lumisections_all:
    n_luminometers_missing = 0
    which_luminometer_missing = -1
    for i, l in enumerate(luminometers):
        if s not in valid_lumisections[l]:
            n_luminometers_missing += 1
            which_luminometer_missing = i
            lumisections_missing[l] += 1
    if n_luminometers_missing == 0:
        lumisections_count[0] += 1
    elif n_luminometers_missing == 1:
        lumisections_count[which_luminometer_missing+1] += 1
    elif n_luminometers_missing == 2:
        lumisections_count[-2] += 1
    else:
        lumisections_count[-1] += 1

for l in luminometers:
    print "%s missing for %d/%d = %.2f%%" % \
        (l, lumisections_missing[l], tot_lumisections, float(100*lumisections_missing[l])/tot_lumisections)

labels = ["All luminometers good (%.1f%%)" % (float(100*lumisections_count[0])/tot_lumisections)]
for i, l in enumerate(luminometers):
    labels.append("Only "+l+" bad (%.1f%%)" % (float(100*lumisections_count[i+1])/tot_lumisections))
labels.append("2 luminometers bad (%.1f%%)" % (float(100*lumisections_count[-2])/tot_lumisections))
labels.append(">2 luminometers bad (%.1f%%)" % (float(100*lumisections_count[-1])/tot_lumisections))

colors = ['forestgreen', 'red', 'blue', 'sienna', 'gold', 'darkviolet', 'lightsalmon']

patches, texts = plt.pie(lumisections_count, colors=colors)
plt.legend(patches, labels, loc="best")
plt.title("Fill validation results in 2018")
plt.axis('equal')
plt.tight_layout()
plt.show()
plt.savefig(output_file_name)
print "Output saved to",output_file_name
