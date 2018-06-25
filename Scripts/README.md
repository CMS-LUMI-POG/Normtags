This directory contains various scripts for working with normtags.

* validateNormtag.sh: A very simple script which validates normtag_BRIL.json by checking to make sure it produces proper output using the 2018 DCSOnly json.

* makeCompositeNT.py: A script that takes a set of input normtags and will build an overall normtag using the priority order specified (basically similar to how doFillValidation.py works but allowing you to change the order after the fact). Run with -h to see the options.

* validateInputFile.py: A script to validate input data intended for loading into the lumi DB. It checks to make sure that all lines are well-formed, that there are no NaN or Inf values, and that the sum of the BX luminosity agrees (reasonably well) with the total luminosity.

* compareTwoCSVsFromBRILCALC.py: Get output per BX from brilcalc using normtag filters. Probably best in bash script as follows:

```bash
for nt in normtag_hfet.json normtag_dt.json normtag_pltzero.json;
  do
    brilcalc lumi --normtag=${nt} -i /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/PromptReco/Cert_294927-306126_13TeV_PromptReco_Collisions17_JSON_MuonPhys.txt -u 'hz/ub' -o ${nt}.csv --output-style=csv --byls --tssec
  done

python Scripts/compareTwoCSVsFromBRILCALC.py normtag_hfet.json.csv normtag_pltzero.json.csv Scripts/NBX_perFill_2017.csv HFPLTFILTER
```
