# Normtags2017
This repository contains the scripts and files for the 2017 normtags.

The fill validation tool doFillValidation.py is used for creating and updating the normtag files. For documentation on how to run this tool, please see [the Twiki page](https://twiki.cern.ch/twiki/bin/view/CMS/FillValidationTool).

The normtag files are:
* normtag_BRIL.json -- overall "offline best lumi" file which chooses the best available luminometer
* normtag_{bcm1f,hfet,hfoc,pltzero}.json -- individual luminometer normtag files with the valid lumisections for that luminometer
* normtag_DATACERT.json -- normtag file after data certification

The log file fillValidationLog.json contains the log information from the fill validation tool.

The other scripts (get_recentfill.py and lumiValidate.py) are used by doFillValidation.py.
