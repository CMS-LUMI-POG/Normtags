#!/usr/bin/env python

# A very simple script to make sure that one or more JSON files are valid. This uses the Python JSON module
# which gives somewhat more helpful error messages than brilcalc does, so it's hopefully easier to track down
# where the exact problem is if one exists.

import json
import sys

if len(sys.argv) < 2:
    print "Usage: "+sys.argv[0]+" [JSON file(s)]"
    sys.exit(1)

for filename in sys.argv[1:]:
    f = open(filename)
    j = json.load(f)
    print "File "+filename+" loaded OK."
