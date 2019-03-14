#!/usr/bin/env python


#import sys (not used!)
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--normtaglist", help="Comma-separated list of normtag (e.g. 'nt1.json,nt2.json')")
parser.add_argument("-o", "--outputfile", default="compositeNT.json", help="output file name")
parser.add_argument("-c", "--normtaglistcomp", default="", help="Comma-separated list of normtag for comparison (e.g. 'nt1.json,nt2.json')")
parser.add_argument("--minrun", default=0,   type=int, help="minimum run number to consider (default:  0)")
parser.add_argument("--maxrun", default=1e7, type=int, help="maximum run number to consider (default:  1e7)")

args=parser.parse_args()
#Used for the comparison normtag.
list_of_known_detectors=["pcc","hfoc","hfet","dt","ramses","pltzero","bcm1f"]

# both args are list of lists where each list is a range of LSs
def RemoveLSs(baseList,listToRM):
    expandedBaseList=[]
    #print "baseList",baseList
    #print "listToRM",listToRM
    for lsRange in baseList:
        for iLS in range(lsRange[0],lsRange[1]+1):
            expandedBaseList.append(iLS)
    
    #print "added all",expandedBaseList
    for lsRange in listToRM:
        for iLS in range(lsRange[0],lsRange[1]+1):
            if iLS in expandedBaseList:
                expandedBaseList.remove(iLS)

    #print "removed some",expandedBaseList
    
    condensedList=[]
    lastLS=0
    for iLS in expandedBaseList:
        if iLS==expandedBaseList[0]:
            condensedList.append([iLS,-1])
        elif iLS-lastLS>1:
            condensedList[-1][1]=lastLS
            condensedList.append([iLS,-1])

        if iLS==expandedBaseList[-1]:
            condensedList[-1][1]=iLS
        lastLS=iLS

    #print condensedList
    return condensedList

##Functions for comparison normtag#########################
def getDictFromJson(jsonFile):
    jsonDict={}
    for line in jsonFile:
        run=int(line[1].keys()[0])
        detc_label=str(line[0])
        lsRanges=line[1][line[1].keys()[0]]
        lsRanges_list=list(lsRanges)
        lsRanges_list.sort()
        for lsRange in lsRanges_list:
            for ls in range(lsRange[0],lsRange[1]+1):
                jsonDict[run,ls]=detc_label
    
    return jsonDict

def getDetcLabel(normtag):
    label="NaN"
    for look_dets in list_of_known_detectors:
        if look_dets in normtag:
            label=look_dets
            break
    return label


def convertDictToJson(jsonDict):
    jsonFormat=[]
    keys=list(jsonDict)
    keys.sort()
    run=keys[0][0]
    prevLS=keys[0][1]
    lastKey=keys[0]
    lastLabel=jsonDict[lastKey]
    range_minval=prevLS
    count=0
    lsRanges=[]
    
    for key in keys:
        count+=1
        ##if new run is found
        if (key[0]!=run or count==len(keys)):
            tempDict={}
            lsRanges.append([range_minval,prevLS])
            tempDict[run]=lsRanges
            jsonFormat.append([lastLabel,tempDict])
            lsRanges=[]
            range_minval=key[1]
            
            if count==len(keys) and key[0]!=run:
                ##Append key[0]
                tempDict={}
                tempDict[key[0]]=[[key[1],key[1]]]
                jsonFormat.append([jsonDict[key],tempDict])
                    
        ##if new label is found
        elif (lastLabel!=jsonDict[key]):
            tempDict={}
            lsRanges.append([range_minval,prevLS])
            tempDict[run]=lsRanges
            jsonFormat.append([lastLabel,tempDict])
            lsRanges=[]
            range_minval=key[1]
        
        elif (key[1]-prevLS > 1):
            lsRanges.append([range_minval,prevLS])
            range_minval=key[1]
        
        
        run=key[0]
        prevLS=key[1]
        lastKey=key
        lastLabel=jsonDict[key]
        
    return jsonFormat  

###################################### Main Program ########################################################################################
normtagslist=args.normtaglist.split(",")

rankAlgo="Default"
print "This script will fill a new normtag with the contents of the given normtags."
if rankAlgo == "Default":
    print "The default ranking algo gives highest priority to the first normtag in the list and lowest priority to the last normtag in the list."


print normtagslist

normtags={}


for normtagfilename in normtagslist:
    ntfile=open(normtagfilename)
    normtags[normtagfilename]=json.load(ntfile)


compositeNT=[]
filledRuns=[]

if rankAlgo=="Default":
    print "go through NTs in the order received"
    print "fill in new list with luminometers if run,ls not covered"
    for normtagfilename in normtagslist:
        for line in normtags[normtagfilename]:
            run=line[1].keys()[0]
            lsRanges=line[1][line[1].keys()[0]]
            if int(run) > args.maxrun or int(run) < args.minrun:
                #print "run",run,args.maxrun,args.minrun,int(run) > args.maxrun, int(run) < args.minrun,int(run) > args.maxrun or int(run) < args.minrun
                continue
            if not compositeNT:
                compositeNT.append(line)
            else:
                #print "find run in list--search whole list--run could be in more than one line"
                iLine=0
                for item in compositeNT:
                    comRun=item[1].keys()[0]
                    #print "if run found remove all LSs already covered"
                    if comRun==run:
                        #print "in com",item
                        #print "to be included",line    
                        lsRanges=RemoveLSs(lsRanges,item[1][run])
                        if not lsRanges:
                            break
                    elif comRun>run:
                        break
                    iLine=iLine+1
                if run not in filledRuns:
                    compositeNT.insert(iLine,line)
                elif lsRanges:
                    # If there's multiple ranges, break them down into individual entries so we can sort them properly later.
                    for thisRange in reversed(lsRanges):
                        newDict={}
                        newDict[run]=[thisRange]
                        compositeNT.insert(iLine,[line[0],newDict])
                
            filledRuns.append(run)


# Sort the final NT so that everything appears in the proper order. Two steps: first sort by first lumisection
# number and then by run.
compositeNT.sort(key=lambda x: x[1].values()[0][0][0])
compositeNT.sort(key=lambda x: int(x[1].keys()[0]))

outputFile=open(args.outputfile,"w")
outputFile.write("[\n")
for line in compositeNT:
    #schade... ths simple way can't be decoded
    #outputFile.write(str(line))
    # example line:    ["hfoc16v1",{"271037":[[1,15]]}],
    outputFile.write("[\""+str(line[0])+"\", {\""+str(line[1].keys()[0])+"\": "+str(line[1][line[1].keys()[0]])+"}]")
    if line != compositeNT[-1]:
        outputFile.write(",\n")
        
outputFile.write("\n]\n")
outputFile.close()
print "Wrote new normtag to",args.outputfile


############################# making second_best normtag (for this use -c option) ###############################
dicts=[]
dict_compare={}
if args.normtaglistcomp!="":
    flagCompare=True
    normtagslist_compare=args.normtaglistcomp.split(",")
    normtags_compare={}
    normtags_id_compares=[]
    for normtagfilename in normtagslist_compare:
        #print ("reading "+ normtagfilename)
        ntfile=open(normtagfilename)
        #load .jsons
        normtags_compare[normtagfilename]=json.load(ntfile)
        #Separate each ls and store info in a dict[run,ls]="detector_normtag"
        dicts.append(getDictFromJson(normtags_compare[normtagfilename]))
else:
    normtagslist_compare=""
    exit()
print("Generating comparison normtag from: ")
print ("best:"+str(normtagslist)+ "  |  comparison(second best):"+ str(normtagslist_compare))

## Detect for each ls of the compositeNT which the best detector available (avoiding cases like det1/det1). The selection is stored in a dict[run,ls]="detector_normtag"
for line in compositeNT:
    run=int(line[1].keys()[0])
    lsRanges=line[1][line[1].keys()[0]]
    lsRanges_list=list(lsRanges)
    lsRanges_list.sort()
    detc_label=str(line[0])
    label=getDetcLabel(detc_label)
    for lsRange in lsRanges_list:
        for ls in range(lsRange[0],lsRange[1]+1):
            for comp_dict in dicts:
                comp_label="nan"
                try:
                    comp_label=getDetcLabel(comp_dict[run,ls])
                except:
                    continue   
                if (comp_label!="nan" and comp_label!=label):
                    dict_compare[run,ls]=comp_dict[run,ls]
#Store dict[run,ls]="detector_normtag" in Json format to be saved in a file.
compositeNT_compare=convertDictToJson(dict_compare)

#Save result in file
outputFile_comp=open((args.outputfile).split(".")[0]+"_compare.json","w")
outputFile_comp.write("[\n")
for line in compositeNT_compare:
    #schade... ths simple way can't be decoded
    #outputFile.write(str(line))
    # example line:    ["hfoc16v1",{"271037":[[1,15]]}],
    outputFile_comp.write("[\""+str(line[0])+"\",{\""+str(line[1].keys()[0])+"\":"+str(line[1][line[1].keys()[0]])+"}]")
    if line != compositeNT_compare[-1]:
        outputFile_comp.write(",\n")
outputFile_comp.write("\n]\n")
outputFile_comp.close()