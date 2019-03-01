import sys
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--normtaglist", help="Comma-separated list of normtag (e.g. 'nt1.json,nt2.json')")
parser.add_argument("-c", "--normtaglistcomp", default="", help="Comma-separated list of normtag for comparison (e.g. 'nt1.json,nt2.json')")
parser.add_argument("-o", "--outputfile", default="compositeNT.json", help="output file name")

parser.add_argument("--minrun", default=0,   type=int, help="minimum run number to consider (default:  0)")
parser.add_argument("--maxrun", default=1e7, type=int, help="maximum run number to consider (default:  1e7)")

args=parser.parse_args()
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

def mergedRanges(Ranges1,inRange):
    rangesMerged=[]
    print ("Looking for merge",Ranges1,"and",inRange)
    for inrange in inRange:
        for range1 in Ranges1:
            print("looking for ", range1, "in",inrange)
            
            if (range1[0]>=inrange[0]):
                temprange_min=range1[0]
                print ("found",temprange_min)
                if (range1[1]<=inrange[1]):
                    temprange_max=range1[1]
                    print ("found",temprange_max)
                else:
                    temprange_max=inrange[1]
                    print ("found",temprange_max)
            elif (inrange[0]<=range1[1]): 
                temprange_min=inrange[0]
                if (inrange[1]<=range1[1]):
                    temprange_max=inrange[1]
                    print ("found",temprange_max)
                else:
                    temprange_max=range1[1]
                    print ("found",temprange_max)
            if (temprange_min<=temprange_max):
                rangesMerged.append([temprange_min,temprange_max])
    rangesMerged.sort()
        
    print ("Result:",rangesMerged)
    return rangesMerged

def oneLinePerRun(compositeNT):
    tempRun=0
    compositeNT_fixed=[]
    lsMixedInRun=[]
    il=0
    for line in compositeNT:
        il+=1
        lsRanges=line[1][line[1].keys()[0]]
        run=int(line[1].keys()[0])
        
        if run==tempRun:
            print ("**************** equal run found in: ",line,run)
            if il==len(compositeNT):
                newDict={}
                newDict[tempRun]=lsMixedInRun
                print (tempRun,"---->>>",newDict[tempRun])
                compositeNT_fixed.append([line[0],newDict])
        else:
            newDict={}
            newDict[tempRun]=list(lsMixedInRun)
            print (tempRun,"---->>>",newDict[tempRun])
            compositeNT_fixed.append([line[0],newDict])
            del lsMixedInRun[:]
            if il==len(compositeNT):
                compositeNT_fixed.append(line)
        
        tempRun=run
        
        for lsRange in lsRanges:
            lsMixedInRun.append(lsRange)
        lsMixedInRun.sort()
    del compositeNT_fixed[0]
    return compositeNT_fixed
            

normtagslist=args.normtaglist.split(",")
flagCompare=False

if args.normtaglistcomp!="":
    flagCompare=True
    normtagslist_compare=args.normtaglistcomp.split(",")
    normtags_compare={}
    normtags_id_compares=[]
    for normtagfilename in normtagslist_compare:
        print ("reading "+ normtagfilename)
        ntfile=open(normtagfilename)
        normtags_compare[normtagfilename]=json.load(ntfile)
        for look_dets in list_of_known_detectors:
            if look_dets in normtagfilename:
                normtags_id_compares.append(look_dets)
                break
    if len(normtagslist_compare)!=len(normtags_id_compares):
        print("Some detector are not found in the known detector list. Please add it")
        exit
    print (normtags_id_compares)
else:
    normtagslist_compare=""
    
rankAlgo="Default"
print ("This script will fill a new normtag with the contents of the given normtags.")
if rankAlgo == "Default":
    print ("The default ranking algo gives highest priority to the first normtag in the list and lowest priority to the last normtag in the list.")


print (normtagslist,normtagslist_compare)

normtags={}
normtags_ids=[]


for normtagfilename in normtagslist:
    print ("reading "+ normtagfilename)
    ntfile=open(normtagfilename)
    normtags[normtagfilename]=json.load(ntfile)
    for look_dets in list_of_known_detectors:
        if look_dets in normtagfilename:
            normtags_ids.append(look_dets)
            break
if len(normtagslist)!=len(normtags_ids):
        print("Some detector are not found in the known detector list. Please add it")
        exit

compositeNT=[]
compositeNT_compare=[]
filledRuns=[]
filledRuns_int=[]

if rankAlgo=="Default":
    print ("go through NTs in the order received")
    print ("fill in new list with luminometers if run,ls not covered")
    for normtagfilename in normtagslist:
        for line in normtags[normtagfilename]:
            run=line[1].keys()[0]
            lsRanges=line[1][line[1].keys()[0]]
            if int(run) > args.maxrun or int(run) < args.minrun:
                print ("run",run,args.maxrun,args.minrun,int(run) > args.maxrun, int(run) < args.minrun,int(run) > args.maxrun or int(run) < args.minrun)
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
                    newDict={}
                    newDict[run]=lsRanges
                    compositeNT.insert(iLine,[line[0],newDict])
                
            filledRuns.append(run)
            filledRuns_int.append(int(run))
## Reorganize to use only 1 line for each run (guessing that runs are sorted)
compositeNT_fixed=oneLinePerRun(compositeNT)

## Reorganize all comparison to use only 1 line for each run (guessing that runs are sorted)
for normtagfilename in normtagslist_compare:
    temp_normtag_compare=oneLinePerRun(normtags_compare[normtagfilename])
    normtags_compare[normtagfilename]=temp_normtag_compare
    print (temp_normtag_compare)

##Save compositeNT in file        
compositeNT=compositeNT_fixed
outputFile=open(args.outputfile,"w")
outputFile.write("[\n")

for line in compositeNT:
    #schade... ths simple way can't be decoded
    #outputFile.write(str(line))
    # example line:    ["hfoc16v1",{"271037":[[1,15]]}],
    outputFile.write("[\""+str(line[0])+"\",{\""+str(line[1].keys()[0])+"\":"+str(line[1][line[1].keys()[0]])+"}]")
    if line != compositeNT[-1]:
        outputFile.write(",\n")
outputFile.write("\n]\n")
outputFile.close()

tempRun=0
same_run=False
if rankAlgo=="Default" and flagCompare:
    for line in compositeNT:
        run=int(line[1].keys()[0])
        if(run==tempRun):
            same_run=True
        else:
            same_run = False
            
        print(run)
        lsRanges=line[1][line[1].keys()[0]]
        #Check if lsRanges is avaliable in the first, second ... comparison detector
        for normtagfilename in normtagslist_compare:
            #remove det1/det1 posibility
            if normtags_compare[normtagfilename][0][0]==line[0]:
                print("passed",normtagfilename,run)
                continue
            print (line[0],normtags_compare[normtagfilename][0][0])
            
            for line_c in normtags_compare[normtagfilename]:
                #print (line_c)
                # Looking for run in normtagfilename
                #print (int(run),int(line_c[1].keys()[0]))
                run_c=int(line_c[1].keys()[0])
                if run == run_c:
                    print ("here!!!!",normtagfilename)
                    line[0]=line_c[0]
                    print (line)
                    ###Still need run selection checking and ls merging
                    line[1][line[1].keys()[0]] = mergedRanges(line_c[1][line_c[1].keys()[0]],lsRanges)
                    compositeNT_compare.append(line)
                    break
        tempRun=run

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


