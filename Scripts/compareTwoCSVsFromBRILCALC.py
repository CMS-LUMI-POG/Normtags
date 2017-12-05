import sys
import ROOT
ROOT.gROOT.SetBatch(ROOT.kTRUE)

##example calls to brilcalc
##
#for nt in ../Normtags/normtag_hfet.json ../Normtags/normtag_dt.json  ../Normtags/normtag_pltzero.json ;
#  do
#    brilcalc lumi --normtag=${nt} -i /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/PromptReco/Cert_294927-306126_13TeV_PromptReco_Collisions17_JSON_MuonPhys.txt    -u 'hz/ub' -o ${nt}.csv --output-style=csv --byls --tssec
#  done




def dictFromCSVFile(file):
    lines=file.readlines()
    dict={}
    for line in lines:
        try:
            items=line.replace(':',',').split(",")
            dict[(int(items[1]),int(items[0]),int(items[2]))]=[int(items[4]),float(items[8])]
        except:
            pass
    print "read", file
    return dict

filename1=sys.argv[1]
filename2=sys.argv[2]
nBXfileName=sys.argv[3]
filelabel=str(sys.argv[4])

NBXPerFill={}
nbxfile=open(nBXfileName)
for line in nbxfile.readlines():
    items=line.split(",")
    try:
        fill=int(items[0])
        NBX=int(items[1])
        NBXPerFill[fill]=NBX
    except:
        print "Problem with line",line

nbxfile.close()

nBX=1

time0=0

file1=open(filename1)
file2=open(filename2)

dict1=dictFromCSVFile(file1)
dict2=dictFromCSVFile(file2)

total1=0
total2=0

total1PerFill={}
total2PerFill={}

overtlapKeys=list(set(dict1).intersection(dict2))
overtlapKeys.sort()

#print len(dict1),len(dict2),len(overtlapKeys)

label=filename2.split("_")[0]+"/"+filename1.split("_")[0]
combineNLS=15

can=ROOT.TCanvas("can","",700,700)
ratio=ROOT.TH1F("ratio",";ratio "+label+";",200,0,2)

ratioNarrow=ROOT.TH1F("ratioNarrow",";ratio "+label+";",200,0.90,1.10)
#these are place holders, to gather averages, should be an easier way to do this
ratioNarrowRun=ROOT.TH1F("ratioNarrowRun",";ratio "+label+";",200,0.90,1.10)
ratioNarrowFill=ROOT.TH1F("ratioNarrowFill",";ratio "+label+";",200,0.90,1.10)
#these are the actual histograms filled by these placeholder averages

ratioVsTime=ROOT.TGraph()
ratioVsInst=ROOT.TGraph()
ratioVsInstProfile=ROOT.TProfile("ratioVsInstProfile",";Average Inst. Luminosity (Hz/#muB);Average "+label,50,0,8)
ratioVsTime.SetTitle(label+";Time (s);Ratio per "+str(combineNLS))
ratioVsInst.SetTitle(";Average Inst. Luminosity (Hz/#muB);"+label)
ratioVsInst_perFill={}

fout = ROOT.TFile(str(sys.argv[4])+"_monitor_plots.root", "recreate")

baddies={}
veryOffLS={}
iCount=1
iBin=0
num=0
den=0
iRatio=0

averageRatioOfRun=0
averageRatioOfFill=0
currentRun=1
currentFill=1
binRun=0
binFill=0

ratioRun=ROOT.TGraphErrors()
ratioFill=ROOT.TGraphErrors()
ratioRun.SetTitle(label+";Run;Ratio")
ratioFill.SetTitle(label+";Fill;Ratio")

for key in overtlapKeys:
    try:
        if not total1PerFill.has_key(key[0]):
            print "setting total to 0 for fill", key[0]
            total1PerFill[key[0]]=0
            total2PerFill[key[0]]=0
        if iCount==1:
            time0=dict1[key][0]
            currentFill=key[0]
            currentRun=key[1]
        if abs(dict1[key][1]/dict2[key][1]-1)>.2:
            newKey=(key[0],key[1])
            newKey=key[0]
            if not ratioVsInst_perFill.has_key(newKey):
                ratioVsInst_perFill[newKey]=ROOT.TGraph()
                iRatio=0
            if newKey not in baddies:
                baddies[newKey]=1
            else:
                baddies[newKey]=baddies[newKey]+1
        if abs(dict1[key][1]/dict2[key][1]-1)>.5:
            if not veryOffLS.has_key(key[1]):
                veryOffLS[key[1]]=[]
            veryOffLS[key[1]].append(key[2])]
            print "50 % off",key, dict1[key][1], dict2[key][1]
            continue
        num=num+dict2[key][1]
        den=den+dict1[key][1]
        total2=total2+dict2[key][1]
        total1=total1+dict1[key][1]
        total1PerFill[key[0]]=total1PerFill[key[0]]+dict1[key][1]
        total2PerFill[key[0]]=total2PerFill[key[0]]+dict2[key][1]

        if iCount%combineNLS==0:
            ratio.Fill(num/den)
            ratioNarrow.Fill(num/den)
            ratioNarrowRun.Fill(num/den)
            ratioNarrowFill.Fill(num/den)
            ratioVsTime.SetPoint(iBin,dict1[key][0]-time0,num/den)
            ratioVsInst.SetPoint(iBin,den/NBXPerFill[key[0]]/combineNLS,num/den)
            ratioVsInstProfile.Fill(den/NBXPerFill[key[0]]/combineNLS,num/den)
            ratioVsInst_perFill[newKey].SetPoint(iRatio, den/NBXPerFill[key[0]]/combineNLS,num/den)
            num=0
            den=0
            iBin=iBin+1
            iRatio=iRatio+1

            if currentRun != key[1]:
                ratioRun.SetPoint(binRun,currentRun,ratioNarrowRun.GetMean())
                if ratioNarrowRun.GetMean()>1.03 or ratioNarrowRun.GetMean()<0.97:
                    print currentRun
                currentRun = key[1]
                binRun = binRun + 1
                if abs(1-ratioNarrowRun.GetMean()) >0.2:
                    print "fill ",currentRun,"ratio is",ratioNarrowRun.GetMean()
                ratioNarrowRun.Reset()
            if currentFill != key[0]:
                print currentFill,total1PerFill[currentFill],total2PerFill[currentFill]
                ratioFill.SetPoint(binFill,currentFill,ratioNarrowFill.GetMean())
                currentFill = key[0]
                binFill=binFill+1
                if abs(1-ratioNarrowFill.GetMean()) >0.2:
                    print "fill ",currentFill,"ratio is",ratioNarrowFill.GetMean()
                ratioNarrowFill.Reset()

        iCount=iCount+1

    except:
        pass


offRuns=veryOffLS.keys()
offRuns.sort()
for run in offRuns:
    veryOffLS[run].sort()
    print run,veryOffLS[run]


ratioVsInst.GetYaxis().SetRangeUser(0.95,1.05)
ratioVsInst.GetXaxis().SetRangeUser(2,8)
ratioVsInst.Draw("AP")
can.Update()
can.SaveAs(filelabel+"_vsInstLumi.png")


fout.WriteTObject(can,filelabel+"_vsInstLumi.png")
ratioVsInstProfile.SetLineColor(ROOT.kRed)
ratioVsInstProfile.Draw()
#ratioVsInstProfile.GetYaxis().SetRangeUser(0.95,1.08)
#p3 = ROOT.TF1("p3","[0]*x+[1]*x*x+[2]*x*x*x",0,10)
ratioVsInstProfile.Fit("pol1")
can.Update()
can.SaveAs(filelabel+"_vsInstLumiPro.png")
fout.WriteTObject(can,filelabel+"_vsInstLumiPro.png")
ratio.Draw()
can.Update()
ratioNarrow.Draw()
print "binned ratio RMS",ratioNarrow.GetRMS()
can.Update()
can.SaveAs(filelabel+"_binnedRatio.png")
fout.WriteTObject(can,filelabel+"_binnedRatio.png")
ratioVsTime.Draw("AP")
can.Update()
can.SaveAs(filelabel+"_vsTime.png")
fout.WriteTObject(can,filelabel+"_vsTime.png")


line_Plot = ROOT.TGraphErrors()
ip=0
line_hist_weighted = ROOT.TH1F("line_hist_weighted", "line_hist_weighted", 100, -0.015, 0.015)
line_hist = ROOT.TH1F("line_hist", "line_hist", 100, -0.015, 0.015)
for key_fill in ratioVsInst_perFill.keys():
    try:
        ratioVsInst_perFill[key_fill].Fit("pol1", "M")
        fitResult = ratioVsInst_perFill[key_fill].GetFunction("pol1")
        #ratioVsInst_perFill[key_fill].Draw()
        #can.Update
        #can.SaveAs(filelabel+"Linearity_"+str(key_fill)+".png")
        value = fitResult.GetParameter(1)
        error = fitResult.GetParError(1)
        if error> 0.0008:
            continue
        line_Plot.SetPoint(ip, float(key_fill), value)
        line_Plot.SetPointError(ip, 0, error)
        line_hist_weighted.Fill(value, total1PerFill[key_fill])
        line_hist.Fill(value)
        fout.WriteTObject(ratioVsInst_perFill[key_fill], str(key_fill)+"ratio")
        ip+=1
        line_Plot.GetXaxis().SetTitle("Fill Number")
    except:
        print "give up"

can.Update
can.SetTickx()
can.SetTicky()
line_Plot.SetMarkerStyle(ROOT.kFullCircle)
line_Plot.GetYaxis().SetRangeUser(-0.02, 0.02)
line_Plot.GetYaxis().SetTitle("p_{1} [(Hz/ub)^{-1}]")
line_Plot.GetXaxis().SetTitle("Fill Number")
line_Plot.Draw("APE")
can.SaveAs(filelabel+"Linearity_perFill.png")
fout.WriteTObject(can,"linearity_perFill")


ratioRun.Draw("APE")
can.SaveAs(filelabel+"_ratioPerRun.png")

ratioFill.Draw("APE")
can.SaveAs(filelabel+"_ratioPerFill.png")

line_hist_weighted.Draw("hist")
print "mean slope, rms",line_hist_weighted.GetMean(),line_hist_weighted.GetRMS()
can.SaveAs(filelabel+"_binnedLinearity.png")

fout.WriteTObject(line_Plot,"line_Plot")
fout.WriteTObject(line_hist,"line_hist")
fout.WriteTObject(line_hist_weighted,"line_hist_wighted")
fout.WriteTObject(ratioVsTime,"ratioVsTime")
fout.WriteTObject(ratioVsInst,"ratioVsInst")
fout.WriteTObject(ratioVsInstProfile,"ratioVsInstProfile")
fout.WriteTObject(ratioRun,"ratioRun")
fout.WriteTObject(ratioFill,"ratioFill")
fout.Close()
