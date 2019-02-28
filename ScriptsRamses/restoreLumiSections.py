#!/usr/bin/env python

# This script will take a list of lumisections that were incorrectly invalidated by the automatic spike
# cleaning algorithm (or any other reason I suppose) and restore them to the normtag (and also delete their
# entries from the log file). You need three arguments:
# - a text file containing the list of lumisections, in the form 6638 315640:56
# - the name of the luminometer
# - the name of the fill validation log file
# Then just run it and it'll do the rest!
#
# Note: the script assumes that in all cases, it's only single lumisections that have been invalidated. If you
# have longer stretches, you'll have to handle them manually -- sorry about that!

import argparse, json

parser = argparse.ArgumentParser()
parser.add_argument("section_list_file", help="Name of file containing list of sections to restore")
parser.add_argument("luminometer_name", help="Name of luminometer to restore sections for")
parser.add_argument("fill_validation_log", help="Name of fill validation log file")
args = parser.parse_args()

normtag_file = "normtag_%s.json" % (args.luminometer_name)

# Read in the fill validation log and the normtag file.
with open(args.fill_validation_log) as fill_json:
    parsed_log_data = json.load(fill_json)

with open(normtag_file) as normtag_json:
    parsed_normtag = json.load(normtag_json)

# Now read the list of sections.
with open(args.section_list_file) as section_list:
    sectionlines = section_list.readlines()
    for l in sectionlines:
        fields = l.rstrip().split(" ")
        fill = int(fields[0])
        runls = fields[1]
        runlsbits = fields[1].split(":")
        run = int(runlsbits[0])
        ls = int(runlsbits[1])
        #print fill,run,ls

        # Find the entry in the fill validation log and delete it.
        found_entry = False
        for log_entry in parsed_log_data:
            if log_entry['fill'] != fill:
                continue
            for i, inval_entry in enumerate(log_entry['invalidated_lumisections']):
                if inval_entry['luminometer'] == args.luminometer_name and inval_entry['beginAt'] == runls and inval_entry['endAt'] == runls:
                    log_entry['invalidated_lumisections'].pop(i)
                    found_entry = True
                    break
            if found_entry == True:
                break
        if not found_entry:
            print "Warning: failed to find log entry for fill",fill,"run:ls",runls

        # Find the entry in the normtag and patch the two surrounding bits. Note: we can only deal with
        # normtags that only have one range per line, sorry about that!

        found_entry = False
        for i, entry in enumerate(parsed_normtag):
            l = entry[0]
            these_runs = entry[1].keys()
            assert(len(these_runs) == 1)
            this_run = these_runs[0]
            assert(len(entry[1][this_run]) == 1)

            # that expression on the right pulls the end of the specified range. yeah, it's ugly, sorry
            if run == int(this_run) and entry[1][this_run][0][1] == (ls-1):
                # Now get the NEXT one and see if it matches the other end of the hole.
                next_entry = parsed_normtag[i+1]
                assert(next_entry[0] == l)
                next_run = next_entry[1].keys()[0]

                if (next_run == this_run): 
                    # This lumisection represents a hole in the entry for this run, so patch up the hole using
                    # the next entry as well.
                    
                    # There could be a legitimate reason for this assertion to fail if multiple LSes have been
                    # invalidated together but we're only restoring one, but this is a little out of scope at
                    # the moment. If this assertion fires, just take the offending line(s) out of your text
                    # file and deal with those manually.
                    assert(next_entry[1][next_run][0][0] == ls+1)

                    # Okay! Now that everything checks out fix the entry so it actually ends at the end of the
                    # next entry, delete that next entry, and get out of here.
                    entry[1][this_run][0][1] = next_entry[1][next_run][0][1]
                    parsed_normtag.pop(i+1)
                    found_entry = True
                    break
                else:
                    # Apparently the lumisection is simply the last one in the run, so fixing it is much simpler in this case.
                    entry[1][this_run][0][1] += 1
                    found_entry = True
                    break

        if found_entry == False:
            print "Warning: failed to find normtag entry for fill",fill,"run:ls",runls

# Made it! Write everything out. Note: borrow the function for writing out the JSON slightly more nicely from
# doFillValidation.py so we don't actually wreck the formatting.

print "Restored",len(sectionlines),"lumi sections."

def writeFormattedJSON(obj, fp, sortKeys):
    output_lines = []
    for i in obj:
        output_lines.append(json.dumps(i, sort_keys=sortKeys))
    fp.write("[\n")
    fp.write(",\n".join(output_lines))
    fp.write("\n]\n")

with open(args.fill_validation_log, 'w') as log_output:
    writeFormattedJSON(parsed_log_data, log_output, True)
print "Successfully updated log file", args.fill_validation_log
with open(normtag_file, 'w') as normtag_output:
    writeFormattedJSON(parsed_normtag, normtag_output, False)
print "Successfully updated normtag file", normtag_file
