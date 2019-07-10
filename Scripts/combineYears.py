#!/usr/bin/env python

import math, sys, argparse, csv

# This script will combine the luminosities for different years with uncertainties as specified in the input
# text file. The file should have the format:
#
# Description,               Corr,2015,2016,2017,2018
# Luminosity,                -,   4.21,40.99,49.79,67.86
# Length scale,              C,   0.5, 0.8, 0.3, 0.2
# Orbit drift,               C,   0.2, 0.1, 0.2, 0.1
# ...
# where the first line has the list of years
# the second line has the list of luminosities
# and the all subsequent lines have, for each uncertainty, the correlation for that uncertainty and the value
# (in %) of that uncertainty for each year.
# The correlation should be 'C' for fully correlated uncertainties, 'U' for uncorrelated uncertainties, or for
# partially correlated, P## where ## is the percent correlation (e.g. 'P70' for a 70% correlated uncertainty).

parser = argparse.ArgumentParser()
parser.add_argument('inputFile', help='Input file')
args = parser.parse_args()

correlations = {}
uncertainties = {}
with open(args.inputFile) as csv_file:
    reader = csv.reader(csv_file, skipinitialspace=True)
    i = 0
    for row in reader:
        if len(row) == 0 or row[0][0] == '#':
            continue
        if i == 0:
            if len(row) <= 2:
                print "Error: expected some years in the top line"
                sys.exit(1)
            years = row[2:]
        elif i == 1:
            if row[0] != 'Luminosity':
                print "Error: expected first row to have luminosity"
                sys.exit(1)
            lumis = [float(x) for x in row[2:]]
            if len(years) != len(lumis):
                print "Error: number of lumis specified doesn't match number of years"
                sys.exit(1)
        else:
            if len(row) != len(lumis)+2:
                print "Error: number of uncertainties for",row[0],"doesn't match number of years"
                sys.exit(1)
            if row[1] != 'C' and row[1] != 'U' and row[1][0] != 'P':
                print "Error: correlation should be C, U, or P##"
                sys.exit(1)
            correlations[row[0]] = row[1]
            uncertainties[row[0]] = [float(x)/100 for x in row[2:]]
        i += 1

# Now add them all up!
total_luminosity = sum(lumis)
total_uncertainty_sq = 0
for u in uncertainties:
    if correlations[u] == 'C':
        # Correlated -- just add up individual uncertainties
        this_uncertainty = 0
        for i in range(len(years)):
            this_uncertainty += uncertainties[u][i]*lumis[i]
        total_uncertainty_sq += this_uncertainty**2
    elif correlations[u] == 'U':
        # Uncorrelated -- add in quadrature
        this_uncertainty_sq = 0
        for i in range(len(years)):
            this_uncertainty_sq += (uncertainties[u][i]*lumis[i])**2
        total_uncertainty_sq += this_uncertainty_sq
    elif correlations[u][0] == 'P':
        # Partially correlated
        frac_correlated = int(correlations[u][1:])/100.0
        this_uncertainty_corr = 0
        this_uncertainty_uncorr_sq = 0
        for i in range(len(years)):
            # Split up the SQUARED uncertainty into correlated and uncorrelated components.
            this_term_corr_sq = ((uncertainties[u][i]*lumis[i])**2)*frac_correlated
            this_term_uncorr_sq = ((uncertainties[u][i]*lumis[i])**2)*(1-frac_correlated)
            this_uncertainty_corr += math.sqrt(this_term_corr_sq)
            this_uncertainty_uncorr_sq += this_term_uncorr_sq
        total_uncertainty_sq += this_uncertainty_corr**2 + this_uncertainty_uncorr_sq

total_uncertainty = math.sqrt(total_uncertainty_sq)
print "Total luminosity is %.2f +/- %.2f (uncertainty of %.2f%%)" % \
    (total_luminosity, total_uncertainty, 100*total_uncertainty/total_luminosity)
                
