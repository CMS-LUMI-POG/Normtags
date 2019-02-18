#!/usr/bin/python

import os, sys

# This script compares the pattern of filled bunches in HF and PLT to see if either has shifted
# from the expected pattern. By default, it will run over all 2017 fills, so you probably want
# to direct the output to a file. You can also run over a subset of fills by specifying them
# on the command line.

# By default, this will save the output file after you're done, in case you need to do further
# investigation. You can change this by uncommenting the last line.

# Luminometers to compare. The first one in this list will determine the reference pattern
# and the others will be compared to it. Use hfet for 2017-18 and hfoc for 2015-16
luminometerOrder = ['hfet', 'pltzero']

# Any BX with a luminosity greater than bxThresh times the luminosity of the peak BX will
# be considered filled. 0.1 is good for most purposes but for early fills you may need
# to use a higher threshold for HF. For HI fills 0.2 seems to work a little better.
bxThresh = 0.1

# Default fill list: all 2017 fills, minus 6385 which is bad for PLT
fills = ['6417', '6415', '6413', '6411', '6405', '6404', '6402', '6399', '6398', '6397',
         '6396', '6392', '6390', '6389', '6388', '6387', '6386',         '6384', '6382',
         '6381', '6380', '6371', '6370', '6364', '6362', '6360', '6358', '6356', '6355',
         '6351', '6349', '6348', '6347', '6346', '6344', '6343', '6341', '6337', '6336',
         '6325', '6324', '6323', '6318', '6317', '6315', '6314', '6313', '6312', '6311',
         '6309', '6308', '6307', '6306', '6305', '6304', '6303', '6300', '6298', '6297',
         '6295', '6294', '6291', '6288', '6287', '6285', '6284', '6283', '6279', '6278',
         '6276', '6275', '6272', '6271', '6269', '6268', '6266', '6263', '6262', '6261',
         '6259', '6258', '6255', '6253', '6252', '6247', '6245', '6243', '6241', '6240',
         '6239', '6238', '6236', '6230', '6194', '6193', '6192', '6191', '6189', '6186',
         '6185', '6182', '6180', '6179', '6177', '6176', '6175', '6174', '6171', '6170',
         '6169', '6168', '6167', '6165', '6161', '6160', '6159', '6158', '6156', '6155',
         '6152', '6147', '6146', '6143', '6142', '6141', '6140', '6138', '6136', '6123',
         '6119', '6116', '6114', '6110', '6106', '6105', '6104', '6098', '6097', '6096',
         '6094', '6093', '6091', '6090', '6089', '6086', '6084', '6082', '6079', '6072',
         '6061', '6060', '6057', '6055', '6054', '6053', '6052', '6050', '6048', '6046',
         '6044', '6041', '6035', '6031', '6030', '6026', '6024', '6021', '6020', '6019',
         '6018', '6016', '6015', '6012', '5984', '5980', '5979', '5976', '5974', '5971',
         '5966', '5965', '5963', '5962', '5960', '5958', '5954', '5952', '5950', '5946',
         '5942', '5934', '5930', '5920', '5919', '5887', '5885', '5883', '5882', '5880',
         '5878', '5876', '5873', '5872', '5870', '5868', '5865', '5864', '5862', '5856',
         '5849', '5848', '5845', '5842', '5840', '5839', '5838', '5837', '5834', '5833', 
         '5830', '5825', '5824', '5822', '5750', '5749', '5746', '5737', '5730', '5722',
         '5719', '5718', '5717', '5710', '5704', '5699', '5698'
         ]

# Fill list for 2016
fills2016 = ['4925', '4926', '4930', '4935', '4937', '4942', '4945', '4947', '4953', '4954', '4956',
         '4958', '4960', '4961', '4964', '4965', '4976', '4979', '4980', '4984', '4985', '4988',
         '4990', '5005', '5013', '5017', '5020', '5021', '5024', '5026', '5027', '5028', '5029',
         '5030', '5038', '5043', '5045', '5048', '5052', '5056', '5059', '5060', '5068', '5069',
         '5071', '5072', '5073', '5076', '5078', '5080', '5083', '5085', '5091', '5093', '5095',
         '5096', '5097', '5101', '5102', '5105', '5106', '5107', '5108', '5109', '5110', '5111',
         '5112', '5116', '5117', '5149', '5151', '5154', '5161', '5162', '5163', '5169', '5170',
         '5173', '5179', '5181', '5183', '5187', '5194', '5196', '5197', '5198', '5199', '5205',
         '5206', '5209', '5210', '5211', '5213', '5219', '5222', '5223', '5229', '5246', '5247',
         '5251', '5253', '5254', '5256', '5257', '5258', '5261', '5264', '5265', '5266', '5267',
         '5270', '5274', '5275', '5276', '5277', '5279', '5282', '5287', '5288', '5330', '5331',
         '5332', '5338', '5339', '5340', '5345', '5351', '5352', '5355', '5370', '5385', '5386',
         '5391', '5393', '5394', '5395', '5401', '5405', '5406', '5412', '5416', '5418', '5421',
         '5422', '5423', '5424', '5426', '5427', '5433', '5437', '5439', '5441', '5442', '5443',
         '5446', '5448', '5450', '5451', '5456',
         # HI fills at 4Z TeV. The first four of these will produce a bunch of problems for PLT
         # because the threshold issues were causing the data to be split between adjacent BXes.
         '5505', '5506', '5507', '5510', '5513', '5514',
         # HI fills at 6.5Z TeV (except for 5575 which was back at 4Z).
         '5519', '5520', '5521', '5522', '5523', '5524', '5526', '5527', '5528', '5533', '5534',
         '5538', '5545', '5546', '5547', '5549', '5550', '5552', '5553', '5554', '5558', '5559',
         '5562', '5563', '5564', '5565', '5568', '5569', '5570', '5571', '5573', '5575']

# If an individual fill (or fills) is/are specified on the command line, use those instead
if (len(sys.argv) > 1):
    fills = sys.argv[1:]

for fill in fills:
    filledBXTemplate = []
    firstAvgLumi = 0

    for luminometer in luminometerOrder:
        printedBunchPattern = False
        print "Getting bunch data for "+luminometer+" fill "+fill+"...please wait..."
        dataFile = "bxdata_"+fill+"_"+luminometer+".csv"

        if not os.path.exists(dataFile):
            os.system('brilcalc lumi --xing -b "STABLE BEAMS" -u hz/ub -f '+fill+' --type '+luminometer+' --xingTr '+str(bxThresh)+' -o '+dataFile)

        print "Checking bunch data for "+luminometer+"..."
        
        infile = open(dataFile, 'r')
        for line in infile:
            fields = line.split(',')
            if (fields[0][0] == '#'):
                continue # skip headers
            
            # Next, split up the individual BX data. Use the slice
            # to drop the initial and final brackets.
            filledBX = []
            if (fields[9][0:2] == '[]'):
                bxFields = []
            else:
                bxFields = fields[9][1:-1].split(' ')
            avgLumi = 0
            # Find the filled BXes and the luminosity in them.
            for i in range(0, len(bxFields), 3):
                filledBX.append(int(bxFields[i]))
                avgLumi += float(bxFields[i+1])
            
            if len(filledBX) > 0:
                avgLumi /= len(filledBX)
                
            # If this is the first LS we've examined, store this as the reference BX pattern.
                
            if (len(filledBXTemplate) == 0):
                filledBXTemplate = list(filledBX)
                shiftedTemplate = list(filledBXTemplate)
                firstAvgLumi = avgLumi
                if len(filledBX) > 0:
                    print "Found",len(filledBX),"filled bunch crossings."

            # Print out the full bunch pattern. This is really only useful when debugging fills
            # with small numbers of filled bunches, not so useful for 2200 bunch fills. Hence
            # the reason it's off by default.
            if False and not printedBunchPattern and len(filledBX) > 0:
                print "Bunch pattern:",
                lastBunch = -9 # number of last filled bunches
                trainCount = 0 # number of bunches in current train
                for i in filledBX:
                    if (i != lastBunch+1):
                        # Isolated/leading bunch
                        # Print out end of previous train, if we were in one
                        if (trainCount > 0):
                            print "T"+str(trainCount),
                        print str(i),
                        trainCount = 1
                    else:
                        # Train bunch
                        trainCount += 1
                    lastBunch = i
                # Don't forget to finish the train we were working on at the end
                if (trainCount > 0):
                    print "T"+str(trainCount),
                print
                printedBunchPattern = True

            # Otherwise, see if this matches the reference BX pattern.
            else:
                if (filledBXTemplate != filledBX):
                    # Maybe the fill dropped a little before the STABLE BEAMS
                    # flag cleared, or we're in a miniscan. Check the average lumi
                    # to see if it decreased a lot. If so, a mismatch is pretty
                    # harmless.
                    if (avgLumi < firstAvgLumi*0.1):
                        print "Probably harmless mismatch in "+luminometer+ " (much lower lumi) in run:fill "+fields[0]+" ls "+fields[1]
                    else:
                        # Try to narrow down the cause a bit. Is it that the number of bunches has changed,
                        # or is there a shift present?
                        if (len(filledBXTemplate) != len(filledBX)):
                            print "Mismatch in numBX "+luminometer+" run:fill "+fields[0]+" ls "+fields[1]+": expected "+str(len(filledBXTemplate))+" got "+str(len(filledBX))
                        else:
                            # The number of bunches found is the same, but the individual bunches don't match up.
                            # Probably there is a shift. Let's see if we can find it.
                            # If this matches the shift from the last time, then we don't need to do any work!
                            # Only check the shift if it doesn't.
                            if (shiftedTemplate != filledBX):
                                foundShift = 0
                                shiftedTemplate = list(filledBXTemplate)
                                for i in range(1, 3564):
                                    for j in range(0, len(shiftedTemplate)):
                                        shiftedTemplate[j] += 1
                                        if (shiftedTemplate[j] > 3564):
                                            shiftedTemplate[j] -= 3564

                                    shiftedTemplate.sort()
                                    if (filledBX == shiftedTemplate):
                                        foundShift = i
                                        break

                            # Now print out the shift if we found it.
                            if (foundShift == 0):
                                # We can't recover the proper bunch pattern just by shifting it. Something more complex is going on...
                                print "Non-simple shift in "+luminometer+ " run:fill "+fields[0]+" ls "+fields[1]
                            else:
                                print luminometer+ " appears to be shifted by "+str(foundShift)+" in run:fill "+fields[0]+" ls "+fields[1]

        # Finished processing this file
        infile.close()
        # Clean up the raw data file.
        # os.remove(dataFile)
