Get output per BX from brilcalc using normtag fitlers. Probably best in bash script.

for nt in normtag_hfet.json normtag_dt.json  normtag_pltzero.json ;
  do
    brilcalc lumi --normtag=${nt} -i /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/PromptReco/Cert_294927-306126_13TeV_PromptReco_Collisions17_JSON_MuonPhys.txt    -u 'hz/ub' -o ${nt}.csv --output-style=csv --byls --tssec
  done



python Scripts/compareTwoCSVsFromBRILCALC.py normtag_hfet.json.csv normtag_pltzero.json.csv Scripts/NBX_perFill_2017.csv  HFPLTFILTER
