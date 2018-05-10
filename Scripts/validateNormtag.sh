#!/bin/bash

# If you need to manually edit a normtag for whatever reason,
# please run this script on it first to make sure that the normtag
# actually works and isn't broken for whatever reason. This uses
# the 2018 DCSOnly json but feel free to change that for other years.

brilcalc lumi --normtag ./normtag_BRIL.json -i /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions18/13TeV/DCSOnly/json_DCSONLY.txt