#!/usr/bin/env python

import os, sys, csv, re

# This script gets the number of colliding bunches per fill. It gets this information from three separate
# sources:
# 1) The WBM information. You will need to provide this yourself by going to the WBM FillReport, getting the
# report for the fill range in question, and then exporting it as a CSV. Then give it as the argument when you
# run this script.
# 2) The number of colliding bunches in the beam configuration as reported from brilcalc beam.
# 3) The number of bunches with significant luminosity for a) hfoc and b) pltzero. "Significant" here is
# defined as 10% of the peak bunch luminosity. However you may need to twiddle this for some fills
# (basically for fills before approximately 5000 the threshold for hfoc needs to be ~0.3 or so).
#
# Ideally all of these will agree. The script will alert you if that is not the case.
#
# In a well-behaved world, you would just need to run this script once and it can automatically delete the
# brilcalc output once it's done with it (deleteAfterProcessing flag below). However in practice I would
# recommend keeping the brilcalc data (leave deleteAfterProcessing to false) because often it will take
# several iterations to deal with more troublesome fills. So you can run it once, keep the data (warning: this
# will take about 20G), and then go back and look at specific fills where the luminometer data has problems
# (in most cases, you can fix these problems by raising the threshold below). Note that if you specify one or
# more fills after the first argument on the command line, it will just look at those fills rather than all of
# the fills in your csv. Once you've fixed all the issues in individual fills, you can run it again for all
# the data to get a (hopefully relatively clean) final output (just grep for the lines with commas and use those).
#
# Note: use hfoc for 2015-16 and hfet for 2017-2018 below.

# As the name suggests, this is the default; it can get changed for heavy-ion runs or with explicit exceptions
# below
defaultLuminometerList = ["hfet", "pltzero"]

# This threshold may also get changed -- also below
defaultBunchThreshold = 0.1

# Whether or not to delete the brilcalc output ater processing.
deleteAfterProcessing = False

# Heavy ion fills. These are treated differently below. Note that for now we only have the 2018 HI fills here.
heavyIonFills = [[7427, 7492]]
luminometerListHI = ["pltzero", "hfoc"]
# Use this threshold for HI fills for HFOC. Can be further overriden below.
thresholdHIHFOC = 0.2 # works best for 2018, 0.3 may be better for earlier years

# Some fills require special handling for the threshold, so those can be specified here.
differentThreshold = {"hfet": {6638: 0.15, 6654: 0.15, 6714: 0.3, 6882: 0.15, 6925: 0.2, 7043: 0.03},
                      "hfoc": {7464: 0.15, 7486: 0.15},
                      "pltzero": {7043: 0.03}
                      }

# For some fills we may need to use an alternate luminometer for whatever reason. This dictionary below lets
# you specify that (in the form of luminometer to be replaced: luminometer to replace it with).
alternateLuminometer = {
    # PLT is missing bunch 16 for some reason in these two fills
    6890: {"pltzero": "bcm1f"},
    6892: {"pltzero": "bcm1f"},
    # very low luminosity fills for which HFET is not reliable
    7300: {"hfet": "hfoc"},
    7407: {"hfet": "hfoc"},
    # HI fills in which PLT data is spread over many bunches for unknown reasons
    7441: {"pltzero": "bcm1f"},
    7453: {"pltzero": "bcm1f"},
    7492: {"pltzero": "bcm1f"}
}

# Some fills we can't reliably use the luminometer data to get the number of bunches, so don't try.
badFills = {"hfoc":
                # For this fills the HF timing was off so the bunches were split between two BXes.
                [3992,
                # In this fill the luminosity varies so much you can't get good results from hfoc
                 4689,
                 ],
            "hfet":
            # In these fills there's spurious luminosity in BX 3490 from the HF laser (HFOC is affected too so
            # we can't just use that), and the overall luminosity is low enough that we can't just change the
            # threshold to eliminate it.
            [6864, 6877, 6879, 6881, 6884, 6885, 6890, 6892, 7043, 7299, 7406],
            "pltzero": 
            # These two the -z and +z sides of the PLT were out of time, so each bunch is split into two.
            # Note: for 3848, 3960, 3962, and 3965, HFOC is also unavailable so I used BCM1F instead to verify.
            [3848, 3960, 3962, 3965, 3971, 3974, 3976, 4322, 4323,
             # Similarly in these fills the PLT alignment is also messed up.
             4207, 4208, 4210, 4211, 4212, 4214,
             # In these fills there is substantial luminosity contribution from some noncolliding bunches
             # (apparently because they generated more background), so the PLT count will be high.
             4499, 4505, 4509, 4510, 4511,
             # Finally in these fills the lumi is so low that the background spillover into the next BX is no
             # longer negligible and we can't exclude them just with thresholds.
             3846, 3847
             ]
            }

# Some fills have such low luminosity that we don't actually see all of the filled bunches in a single lumisection,
# no matter how low we set the threshold. In this case we have to aggregate the filled bunches over several LSes
# in order to actually get the list of filled bunches.
veryLowFills = [3846, 3847, 7299]

# Read the WBM CSV file. This will also define the list of fills that we check against the other sources.

if len(sys.argv) < 2:
    print "Usage: "+sys.argv[0]+" CSVFile [fills]"
    sys.exit(0)

fillList = []
nBunchWBM = {}
nBunchWBMTarget = {}
with open(sys.argv[1]) as csvFile:
    reader = csv.reader(csvFile, delimiter=",")
    for row in reader:
        if row[0].find("Fill") > -1:
            continue
        thisFill = int(row[0])
        thisNBunch = int(row[20])
        targetNBunch = int(row[21])
        fillList.append(thisFill)
#        if (thisNBunch != targetNBunch):
#            print "Warning: for fill",thisFill,"number of colliding bunches =",thisNBunch,"but expected",targetNBunch,"from filling scheme"
        nBunchWBM[thisFill] = thisNBunch
        nBunchWBMTarget[thisFill] = targetNBunch

        # Also check to see if the target bunches match the number in the filling scheme. This should always
        # match but sometimes WBM goes a little weird. A quick explanation of how this works:
        # * Normal filling schemes are 25ns_XXXXb_YYY_ZZZ_..., where the first set of numbers is the number of
        # bunches in each beam and then there are three numbers, the first indicating the number of colliding
        # bunches at IP1/5 (the number we want) and the other two at IP2 and IP8, then a few more details on
        # the injection scheme.
        # * If there's a different number of bunches in each beam (rare, but happens in a few VdM filling
        # schemes for example) then you get 25ns_XXXb_YYYb_ZZZ..., so we want ZZZ in this case.
        # * The lead and xenon filling schemes have "Pb" and "Xe", respectively, instead of "b".
        # * Finally there are a few which just don't fit at all so we handle them manually.

        fillingScheme = row[23]
        nBunchFromScheme = 0
        result = re.search("[0-9]+(?:b|Pb|Xe)_(?:[0-9]+b_)?([0-9]+)", fillingScheme)
        if result:
            nBunchFromScheme = result.group(1)
        else:
            if fillingScheme.find("2nominals_10pilots_lossmaps_coll_allIPs") >= 0:
                nBunchFromScheme = 1
            elif fillingScheme.find("MD3295_B1full_144bpi") >= 0:
                nBunchFromScheme = 12
            elif fillingScheme.find("Multi_525ns_152_150_0_0_8bpi_19inj") >= 0:
                nBunchFromScheme = 150
            else:
                print "Failed to parse filling scheme",fillingScheme
        if int(nBunchFromScheme) != targetNBunch:
            print "Warning: for fill",thisFill,"WBM target bunches =",targetNBunch,"but filling scheme specifies",nBunchFromScheme

# If an individual fill (or fills) is/are specified on the command line, use those instead
if (len(sys.argv) > 2):
    fillList = [int(a) for a in sys.argv[2:]]

for fill in fillList:

    # Set the luminometers to use (at least to start with).
    luminometerList = list(defaultLuminometerList)
    
    # See if we're in a heavy ion fill. If so, change the luminometer list and also set a flag so we can change thresholds below.
    isHeavyIons = False
    for x in heavyIonFills:
        if fill >= x[0] and fill <= x[1]:
            isHeavyIons = True
            luminometerList = list(luminometerListHI)

    # Check to see if this is a fill for which we need to use an alternate luminometer.
    if fill in alternateLuminometer:
        for i in range(len(luminometerList)):
            if luminometerList[i] in alternateLuminometer[fill]:
                luminometerList[i] = alternateLuminometer[fill][luminometerList[i]]
            
    # Get the number of colliding bunches from the beam information.
    beamFileName = "temp_beam_"+str(fill)+".csv"
    if not os.path.exists(beamFileName):
        os.system("brilcalc beam -f "+str(fill)+" -o "+beamFileName)
    
    nBunchBeam = -1
    with open(beamFileName) as beamFile:
        reader = csv.reader(beamFile, delimiter=',')
        for row in reader:
            if row[0][0] == '#':
                continue

            nBunchThisRow = int(row[7])
            if (nBunchBeam == -1):
                nBunchBeam = nBunchThisRow
            else:
                if (nBunchBeam != nBunchThisRow):
                    print "Warning: number of colliding bunches changed during fill",fill

    if (nBunchBeam == -1):
        print "Error: failed to find number of bunches in beam data for fill",fill
    # print "Found",nBunchBeam,"colliding bunches in beam data for fill",fill

    if (deleteAfterProcessing):
        os.remove(beamFileName)

    # Get the number of colliding bunches from the luminometers.
    # This code is taken from compareBXPatterns.py but is much simpler since it only
    # has to worry about the number of colliding BXes, not the pattern.

    nBunchLumi = -1

    for luminometer in luminometerList:
        # Check to see if this luminometer is actually usable for this fill.
        if luminometer in badFills and fill in badFills[luminometer]:
            continue
            
        # Set the threshold.
        bunchThreshold = defaultBunchThreshold
        # higher threshold for HFOC for HI runs
        if luminometer == "hfoc" and isHeavyIons:
            bunchThreshold = thresholdHIHFOC
        # override if specified above
        if luminometer in differentThreshold and fill in differentThreshold[luminometer]:
            bunchThreshold = differentThreshold[luminometer][fill]

        filledBunches = set()
        dataFileName = "bxdata_"+str(fill)+"_"+luminometer+".csv"
        
        if not os.path.exists(dataFileName):
            os.system('brilcalc lumi --xing -b "STABLE BEAMS" -u hz/ub -f '+str(fill)+' --type '+luminometer+' --xingTr '+str(bunchThreshold)+' -o '+dataFileName)

        nlines = 0
        with open(dataFileName) as dataFile:
            reader = csv.reader(dataFile, delimiter=',')
            for row in reader:
                if row[0][0] == '#':
                    continue

                # To save time and annoyance, just consider the first 25 lines of the file, since presumably
                # any differences in the rest of the file are due to either (a) specific luminometer issues
                # (which we don't really care about for this purpose) or (b) a bunch decaying faster than its
                # companions (which can happen but we can't really account for that in our simple total so
                # let's not worry about it). For the aggregated method we may need more lines, however.
                if (nlines > 25 and fill not in veryLowFills) or nlines > 500:
                    break

                # Next, split up the individual BX data. Use the slice
                # to drop the initial and final brackets.
                thisNBunch = 0
                if len(row) < 9:
                    print row
                # If there's no data at all, just skip this row. We'll get an accurate count once we get data.
                if (row[9][0:2] == '[]'):
                    bxFields = []
                    continue
                else:
                    bxFields = row[9][1:-1].split(' ')
                avgLumi = 0

                nlines += 1

                if not (fill in veryLowFills):
                    # "Regular" method: look at the filled BXes LS-by-LS

                    # Find the filled BXes and the luminosity in them.
                    for i in range(0, len(bxFields), 3):
                        thisNBunch += 1
                        avgLumi += float(bxFields[i+1])

                    if thisNBunch > 0:
                        avgLumi /= thisNBunch

                    # If this is the first LS we've examined, store this as the number of BXes.
                    if (nBunchLumi == -1):
                        nBunchLumi = thisNBunch
                        firstAvgLumi = avgLumi
                        # print "Found",nBunchLumi,"filled bunch crossings in",luminometer

                    # Otherwise, see if this matches the number we were expecting.
                    else:
                        if (thisNBunch != nBunchLumi):
                            # Maybe the fill dropped a little before the STABLE BEAMS
                            # flag cleared, or we're in a miniscan. Check the average lumi
                            # to see if it decreased a lot. If so, a mismatch is pretty
                            # harmless.
                            if (avgLumi < firstAvgLumi*0.1):
                                # print "Probably harmless mismatch in "+luminometer+ " (much lower lumi) in run:fill "+row[0]+" ls "+row[1]
                                pass
                            else:
                                print "Mismatch in numBX "+luminometer+" run:fill "+row[0]+" ls "+row[1]+": expected",nBunchLumi,"got",thisNBunch
                    # end of if statement above
                else:
                    # "Alternate" method: aggregate filled bunches over all (first 25) lumisections
                    # Store the filled BX number
                    for i in range(0, len(bxFields), 3):
                        filledBunches.add(bxFields[i])

            # end of loop over rows
        # end of file read

        # If we're using the alternate method, look at the total number of bunches.
        if (fill in veryLowFills):
            thisNBunch = len(filledBunches)
            if (nBunchLumi == -1):
                refFilledBunches = set(filledBunches)
                nBunchLumi = thisNBunch
            elif (thisNBunch != nBunchLumi):
                print "Mismatch in aggregated numBX "+luminometer+": expected",nBunchLumi,"got",thisNBunch,"missing",refFilledBunches-filledBunches

        # Clean up the raw data file.
        if deleteAfterProcessing:
            os.remove(dataFileName)
    
    # end of loop over luminometers
    # print "Found",nBunchLumi,"bunches from luminometer data"

    # OK finally we have all the information. Now let's see if it agrees.
    if (nBunchWBM[fill] == nBunchBeam and nBunchWBM[fill] == nBunchLumi):
        print "Fill",fill,"has",nBunchWBM[fill],"colliding bunches"
    else:
        print "Error: for fill",fill,"WBM reports",nBunchWBM[fill],"beam reports",nBunchBeam,"and luminometers report",nBunchLumi,"colliding bunches"
    print str(fill)+","+str(nBunchWBMTarget[fill])+","+str(nBunchWBM[fill])+","+str(nBunchBeam)+","+str(nBunchLumi)
    sys.stderr.write("Finished fill "+str(fill)+"\n")
