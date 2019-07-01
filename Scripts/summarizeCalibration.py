#!/usr/bin/env python

# This script takes a YAML file defining a normtag and prints out some information about the calibration
# constants that went into it. Note that this doesn't really work very well with the HFOC/HFET normtags
# because the additional correction factors produce very large slope corrections for fills with small numbers
# of bunches -- you might be better off just looking at the numbers in the comments instead.

import sys, re

if len(sys.argv) < 2:
    print "Usage:",sys.argv[0],"INPUT_YAML"
    sys.exit(1)

orbit_freq = 11246.0

# Read input file. Alas, Python YAML parsers exist but they don't seem to be installed on the CMS machines, so
# for maximum compatibility we'll just parse the file ourselves.

sigmavis_vals = []
slope_vals = []
p0_vals = []

in_headers = True
with open(sys.argv[1]) as infile:
    while 1:
        line = infile.readline()
        if not line:
            break

        if not in_headers:
            # Parse the next four lines as a single IOV.
            result = re.search("- (\d+):", line)
            if result:
                run = result.group(1)
            else:
                print "Error: expected to find run number, got",line
                sys.exit(2)

            line = infile.readline()
            result = re.search("func: (.*)", line)
            if result:
                if result.group(1) != "poly1d":
                    print "Error: don't know how to deal with a function that isn't poly1d:", result.group(1)
                    sys.exit(3)
            else:
                print "Error: expected to find function, got",line
                sys.exit(2)

            line = infile.readline()
            result = re.search("payload: {\'coefs\': *\'(.*)\'}", line)
            if result:
                coeffs = [float(i) for i in result.group(1).split(",")]
                if len(coeffs) >= 4 and float(coeffs[-4]) != 0.0:
                    print "Don't really know what to do with a line with a term higher than quadratic:", coeffs[-4]
                    print "This entry will be skipped."
                    line = infile.readline()
                    continue
                p = list(reversed(coeffs))
                while len(p) < 3:
                    p.append(0.0)
                sigmavis = orbit_freq/p[1]
                slope = 100*p[2]/(p[1]*p[1])

                sigmavis_vals.append(sigmavis)
                slope_vals.append(slope)
                p0_vals.append(p[0])
            else:
                print "Error: expected to find payload, got",line

            # Comments line -- not too much to do with this one
            line = infile.readline()
            result = re.search("comments: fill *(\d+) *, *sigvis *([0-9.]+) *, *eff *([0-9.]+) *, *slope *(-?[0-9.]+)", line)

        if re.search("since:", line):
            in_headers = False
    # line loop
# file open

print "sigma_vis*eff ranges from %.2f to %.2f" % (min(sigmavis_vals), max(sigmavis_vals))
if (min(slope_vals) == 0 and max(slope_vals) == 0):
    print "No slope correction"
else:
    print "Slope correction ranges from %.2f to %.2f (%%/(Hz/ub))" % (min(slope_vals), max(slope_vals))
if (min(p0_vals) != 0 or max(p0_vals) != 0):
    print "Constant term ranges from %.2f to %.2f" % (min(p0_vals), max(p0_vals))

