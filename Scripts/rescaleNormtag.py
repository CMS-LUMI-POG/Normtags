#!/usr/bin/env python
# This script takes an existing YAML file and rescales it to match a new sigmavis.  Linearity corrections are
# not affected. Note: the comments in the header will not be changed, so make sure to update them yourself!

# Arguments:
# 1) input YAML file
# 2) new sigmavis
# 3) new target fill number at which the new sigmavis applies

import sys, re

if len(sys.argv) < 4:
    print "Usage:",sys.argv[0],"INPUT_YAML NEW_SIGMAVIS TARGET_FILL"
    sys.exit(1)

new_sigmavis = float(sys.argv[2])
target_fill = int(sys.argv[3])
orbit_freq = 11246.0
output_name = "normtag.yaml"

outfile = open(output_name, "w")

# Read input file. Alas, Python YAML parsers exist but they don't seem to be installed on the CMS machines, so
# for maximum compatibility we'll just parse the file ourselves.

calibration = {}

in_headers = True
with open(sys.argv[1]) as infile:
    while 1:
        line = infile.readline()
        if not line:
            break

        if in_headers:
            outfile.write(line)
        else:
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
            result = re.search("payload: {\'coefs\': *\'(-?[0-9.]+) *, *(-?[0-9.]+) *, *(-?[0-9.]+)\' *}", line)
            if result:
                poly2 = float(result.group(1))
                poly1 = float(result.group(2))
                poly0 = float(result.group(3))
            else:
                print "Error: expected to find payload, got",line

            # The comments in David's YAML files are nice and well-formed, so they should be easy to parse.
            # If you're dealing with YAML files from another source you'll probably need to change this code.
            line = infile.readline()
            result = re.search("comments: fill *(\d+) *, *sigvis *([0-9.]+) *, *eff *([0-9.]+) *, *slope *(-?[0-9.]+)", line)
            if result:
                fill = int(result.group(1))
                sigmavis = float(result.group(2))
                eff = float(result.group(3))
                slope = float(result.group(4))/100
            else:
                print "Error: failed to parse comments line, got",line

            # Check to make sure that the comments actually match the data!
            k = orbit_freq/(sigmavis*eff)
            if poly0 != 0:
                print "Error: 0th order term for",fill,"isn't zero!"
            if abs(k/poly1 - 1) > 0.01:
                print "Error: first order coefficient for",fill,"doesn't match (expected",k,"got",poly1,")"
            if abs(-k*k*slope/poly2 - 1) > 0.01:
                print "Error: second order coefficient for",fill,"doesn't match comments (expected",-k*k*slope,"got",poly2,")"

            #print "Successfully parsed fill",fill
            # Now store all of the data into our dictionary.
            calibration[fill] = {"first_run": run, "poly2": poly2, "poly1": poly1, "sigmavis": sigmavis, "eff": eff, "slope": slope}

        if re.search("since:", line):
            in_headers = False
    # line loop
# file open

# Note that since calculating from the values in the comments doesn't always match the values in the functions
# perfectly, we have two choices for how to calculate the new coefficients: entirely from scratch with the
# given values in the comments but the new sigmavis/efficiency baseline, or by rescaling the existing values
# with the scale factor. For maximum compatibility, I go with the latter.

if target_fill not in calibration:
    print "Error: target fill not found in input YAML file"
    sys.exit(4)

baseline_efficiency = calibration[target_fill]["eff"]
baseline_sigmavis = calibration[target_fill]["sigmavis"]*baseline_efficiency
scale_factor = baseline_sigmavis/new_sigmavis

print "Applied scale factor is %.3f" % (scale_factor)

# Now write out the calibration with the new fill.
for f in sorted(calibration.keys()):
    outfile.write("    - %s:\n" % (calibration[f]["first_run"]))
    outfile.write("        func: poly1d\n")
    outfile.write("        payload: {'coefs': '%.4f,%.6f,0.'}\n" % (calibration[f]["poly2"]*scale_factor*scale_factor,
                                                                  calibration[f]["poly1"]*scale_factor))
    outfile.write("        comments: fill %d, sigvis %.2f, eff %.3f, slope %.3f\n" % (f, new_sigmavis,
                                                                                    calibration[f]["eff"]/baseline_efficiency,
                                                                                    calibration[f]["slope"]*100))

outfile.close()
print "Output written to",output_name
print "Don't forget to update the header!"
