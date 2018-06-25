# Normtags
This repository contains the scripts and files for generating normtags, originally introduced for the 2017 run.

The fill validation tool doFillValidation.py is used for creating and updating the normtag files. For documentation on how to run this tool, please see [the Twiki page](https://twiki.cern.ch/twiki/bin/view/CMS/FillValidationTool).

The normtag files are:
* normtag_BRIL.json -- overall "offline best lumi" file which chooses the best available luminometer
* normtag_{bcm1f,hfet,hfoc,pltzero,dt}.json -- individual luminometer normtag files with the valid lumisections for that luminometer
* normtag_PHYSICS.json -- overall "physics luminosity" file which contains the calibrations that have been approved for physics
* normtag_DATACERT.json -- normtag file after data certification (2015 and 2016 only; as of 2017 this has been obsoleted)

The log file fillValidationLog.json contains the log information from the fill validation tool.

The other scripts (get_recentfill.py and lumiValidate.py) are used by doFillValidation.py.

There are also other scripts for other normtag tasks in the Scripts/ directory. Please see there for documentation.