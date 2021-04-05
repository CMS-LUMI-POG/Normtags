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
#
# Command-line arguments:
# -y YEARS (e.g. -y 2016,2017,2018): add up only these selected years
# -c: force all uncertainties to be treated as correlated
# -u: force all uncertainties to be treated as uncorrelated

parser = argparse.ArgumentParser()
parser.add_argument('inputFile', help='Input file')
parser.add_argument('-y', '--years', help='Comma-separated list of years to use in result')
parser.add_argument('-r', '--ratio', action='store_true', help='Combining two different years at two energies')
group = parser.add_mutually_exclusive_group()
group.add_argument('-c', '--force-correlated', action='store_true', help='Treat all systematics as correlated')
group.add_argument('-u', '--force-uncorrelated', action='store_true', help='Treat all systematics as uncorrelated')
args = parser.parse_args()

years_to_use = None
if args.years:
    years_to_use = args.years.split(",")

correlations = {}
uncertainties = {}
with open(args.inputFile) as csv_file:
    reader = csv.reader(csv_file, skipinitialspace=True)
    i = 0
    for row in reader:
        if len(row) == 0 or row[0][0] == '#':
            continue
        systName=row[0]
        if i == 0:
            if len(row) <= 2:
                print "Error: expected some years in the top line"
                sys.exit(1)
            years = row[2:]
        elif i == 1:
            if systName != 'Luminosity':
                print "Error: expected first row to have luminosity"
                sys.exit(1)
            lumis = [float(x) for x in row[2:]]
            if len(years) != len(lumis):
                print "Error: number of lumis specified doesn't match number of years"
                sys.exit(1)
        else:
            if len(row) != len(lumis)+2:
                print "Error: number of uncertainties for",systName,"doesn't match number of years"
                sys.exit(1)
            if row[1] != 'C' and row[1] != 'U' and row[1][0] != 'P':
                print "Error: correlation should be C, U, or P##"
                sys.exit(1)
            correlations[systName] = row[1]
            uncertainties[systName] = [float(x)/100 for x in row[2:]]
        i += 1

if args.years:
    # If we're only using a subset of years, then go ahead and rebuild the years and lumis arrays
    # with only the ones that we're using.
    use_this_year = []
    new_years = []
    new_lumis = []
    for i, y in enumerate(years):
        if y in years_to_use:
            new_years.append(y)
            new_lumis.append(lumis[i])
        use_this_year.append(y in years_to_use)
    years = new_years
    lumis = new_lumis

    # Now, go through the uncertainties and drop the data for years that we're not using. This is a little
    # clunky but it should work.
    for u in uncertainties:
        new_uncertainties = []
        for i in range(len(uncertainties[u])):
            if use_this_year[i]:
                new_uncertainties.append(uncertainties[u][i])
        uncertainties[u] = new_uncertainties

total_luminosity = sum(lumis)
if args.ratio:
    total_luminosity = lumis[1]/lumis[0]

total_uncertainty_sq = 0
for u in uncertainties:
    if (correlations[u] == 'C' or args.force_correlated) and not args.force_uncorrelated:
        # Correlated -- just add up individual uncertainties
        this_uncertainty = 0
        for i in range(len(years)):
            this_uncertainty += uncertainties[u][i]*lumis[i]
        if args.ratio:
            abs_uncertainty_0=uncertainties[u][0]*lumis[0]
            abs_uncertainty_1=uncertainties[u][1]*lumis[1]
            if abs_uncertainty_0>abs_uncertainty_1:
                this_uncertainty = (lumis[1]/lumis[0])*(math.sqrt( (abs_uncertainty_1/lumis[1])**2 + (abs_uncertainty_0/lumis[0])**2 - 2*abs_uncertainty_1**2/(lumis[0]*lumis[1]) ))
            else:
                this_uncertainty = (lumis[1]/lumis[0])*(math.sqrt( (abs_uncertainty_1/lumis[1])**2 + (abs_uncertainty_0/lumis[0])**2 - 2*abs_uncertainty_0**2/(lumis[0]*lumis[1]) ))
        total_uncertainty_sq += this_uncertainty**2
    elif correlations[u] == 'U' or args.force_uncorrelated:
        # Uncorrelated -- add in quadrature
        this_uncertainty_sq = 0
        for i in range(len(years)):
            this_uncertainty_sq += (uncertainties[u][i]*lumis[i])**2
        if args.ratio:
            abs_uncertainty_0=uncertainties[u][0]*lumis[0]
            abs_uncertainty_1=uncertainties[u][1]*lumis[1]
            this_uncertainty_sq = (lumis[1]/lumis[0])**2*( (abs_uncertainty_1/lumis[1])**2 + (abs_uncertainty_0/lumis[0])**2 )
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
if args.force_correlated:
    print "*** All uncertainties have been treated as correlated ***"
if args.force_uncorrelated:
    print "*** All uncertainties have been treated as uncorrelated ***"
if not args.ratio:
    print "Total luminosity is %.2f +/- %.2f (uncertainty of %.2f%%)" % \
        (total_luminosity, total_uncertainty, 100*total_uncertainty/total_luminosity)
else:
    print "Ratio luminosity is %.2f +/- %.3f (uncertainty of %.2f%%)" % \
        (total_luminosity, total_uncertainty, 100*total_uncertainty/total_luminosity)
                
# Next make the final table for use by other people. The first step is to go through and see if any
# uncertainties are treated as correlated but only are nonzero for one year. If so, we can treat them as
# uncorrelated rather than have to put them as a separate bucket.
for u in uncertainties:
    n_nonzero = 0
    for x in uncertainties[u]:
        if x > 0:
            n_nonzero += 1
    if n_nonzero == 1 and correlations[u] == 'C':
        correlations[u] = 'U'
# Now, for each uncertainty, print it out as is if correlated, but add it to the total uncorrelated bin if
# not.
total_uncorrelated = [0]*len(years)
for u in sorted(uncertainties):
    if correlations[u] == 'C':
        print u+","+",".join([str(x*100) for x in uncertainties[u]])
    elif correlations[u] == 'U':
        for i in range(len(uncertainties[u])):
            total_uncorrelated[i] += (100*uncertainties[u][i])**2
    elif correlations[u][0] == 'P':
        correlated_uncertainty = []
        frac_correlated = int(correlations[u][1:])/100.0
        for i in range(len(years)):
            # Split the uncertainty into correlated and uncorrelated parts.
            this_term_corr_sq = ((100*uncertainties[u][i])**2)*frac_correlated
            this_term_uncorr_sq = ((100*uncertainties[u][i])**2)*(1-frac_correlated)
            # Dump the uncorrelated part into the uncorrelated bucket and keep track of the correlated part.
            total_uncorrelated[i] += this_term_uncorr_sq
            correlated_uncertainty.append("%.1f" % (math.sqrt(this_term_corr_sq)))
        print u+" (correlated part),"+",".join(correlated_uncertainty)
# Finally, print out the uncorrelateds.
for i in range(len(years)):
    output_array = ['0.0']*len(years)
    output_array[i] = "%.1f" % (math.sqrt(total_uncorrelated[i]))
    print "Uncorrelated "+str(years[i])+","+",".join(output_array)



print "\n\nSimplified scheme\n"

mergedUncertSquared={}
for uncert in uncertainties:
    #check which years are correlated
    if correlations[uncert] == 'U':
        for iYear in range(len(years)):
            if not mergedUncertSquared.has_key(years[iYear]):
                mergedUncertSquared[years[iYear]]=[0]
            mergedUncertSquared[years[iYear]][0]+=uncertainties[uncert][iYear]**2
    elif correlations[uncert] == 'C':
        thisSet=""
        nYear=0
        for iYear in range(len(years)):
            if uncertainties[uncert][iYear] > 0:
                thisSet+=years[iYear]
                nYear+=1
        if not mergedUncertSquared.has_key(thisSet):
            mergedUncertSquared[thisSet]=[0]*nYear
        yearInd=0
        for iYear in range(len(years)):
            if uncertainties[uncert][iYear] > 0:
                mergedUncertSquared[thisSet][yearInd]+=uncertainties[uncert][iYear]**2
                yearInd+=1
              

   
yearSets=mergedUncertSquared.keys()
yearSets.sort()
for year in years:
    yearSets.remove(year)
    yearSets.append(year)

for yearSet in yearSets:
    print yearSet,
    for setInd in range(len(mergedUncertSquared[yearSet])):
        print "%.1f" % (math.sqrt(mergedUncertSquared[yearSet][setInd])*100),
    print
     

