#!/usr/bin/python

# doFillValidation.py
# Paul Lujan, June 2017
#
# This takes the various scripts for validating the online luminosity and producing the first
# draft of the online normtag and combines them (or at least attempts to combine them) into one
# simple GUI. This will iterate over the fills that are not yet in the normtag, and for each:
# - display the fill validation plot
# - show the user a list of lumisections that are missing for each luminometer (hopefully none)
# - give the user a chance to invalidate lumisections for a given luminometer, if they see things
#   in the fill validation plot that suggest that these need to be invalidated.
# Once this is done, this will write out the normtags (the overall normtag_BRIL and the normtags
# for the individual luminometers) with the information from the new fill and then proceed to
# the next.

# TODO:
#  - add automatic git commit on completion
#  - save current status so if application is unexpectedly terminated
#    (dropped connection, etc.) the current work isn't lost

from Tkinter import *
import tkMessageBox
import os
import csv
import json
import smtplib
from email.mime.text import MIMEText
import getpass # for username
import socket  # for hostname

# List of luminometers. The first in this list is the one that will be
# used as the baseline reference and so should generally be BCM1F, since
# that is less prone to being out.
luminometers = ['bcm1f', 'pltzero', 'hfoc', 'hfet']

# Default priority order for luminometers.
lumiPriority = ['pltzero', 'hfet', 'bcm1f', 'hfoc']

# Datatag to be used for each luminometer.
datatags = {'pltzero': 'pltzero17v1',
            'hfet': 'hfet17v1',
            'bcm1f': 'bcm1f17v1',
            'hfoc': 'hfoc17v1'}

# Information for automatically sending emails. First, we want to group hfet and hfoc into a single target
# email, so this first dictionary defines that.
emailTargets = {'pltzero': 'pltzero', 'bcm1f': 'bcm1f', 'hfet': 'hf', 'hfoc': 'hf'}
# Second, the list of recipients for each target.
emailRecipients = {'pltzero': ['paul.lujan@cern.ch','andres.delannoy@gmail.com','andreas.kornmayer@cern.ch','joseph.noel.heideman@cern.ch'],
                   'bcm1f': ['Moritz.Guthoff@cern.ch'],
                   'hf': ['capalmer@cern.ch','marlow@princeton.edu','alexis.kalogeropoulos@cern.ch','samuel.lloyd.higginbotham@cern.ch']}

# Paths to various things.
lumiValidatePath = "./lumiValidate.py"         # script for making fill validation plot
getRecentFillPath = "./get_recentfill.py"      # helper script to find most recent fill
logFileName = "./fillValidationLog.json"       # log JSON
bestLumiFileName = "./normtag_BRIL.json"       # best lumi JSON
lumiJSONFileNamePattern = "./normtag_%s.json"  # filename pattern for individual luminometer JSONs
dbAuthFileName = "./db.ini"                    # authentication file for DB
lockFileName = "lock.doFillValidation"         # lock file name

#### Subroutines begin here

# This is the implementation for the dialog window to select new ranges to invalidate.

class InvalidateDialog:
    def __init__(self, parent):
        self.dwin = Toplevel(parent)
        self.dwin.title('Invalidating lumisections...')
        self.titleLabel = Label(self.dwin, text='Invalidating new range')
        self.titleLabel.grid(row=0, column=0, columnspan=3)
        self.luminLabel = Label(self.dwin, text='Luminometer:')
        self.luminLabel.grid(row=1, column=0)
        self.selectedLumin = StringVar(self.dwin)
        self.selectedLumin.set(lumiPriority[0])
        self.luminMenu = apply(OptionMenu, (self.dwin, self.selectedLumin)+tuple(lumiPriority))
        self.luminMenu.grid(row=1, column=1)
        self.startLabel = Label(self.dwin, text='Starting run:LS:')
        self.startLabel.grid(row=2, column=0)
        self.startAt = Entry(self.dwin)
        self.startAt.grid(row=2, column=1)
        self.startBonusLabel = Label(self.dwin, text='(or -1 for start of fill)')
        self.startBonusLabel.grid(row=2, column=2)
        self.endLabel = Label(self.dwin, text='Ending run:LS:')
        self.endLabel.grid(row=3, column=0)
        self.endAt = Entry(self.dwin)
        self.endAt.grid(row=3, column=1)
        self.startBonusLabel = Label(self.dwin, text='(or -1 for end of fill)')
        self.startBonusLabel.grid(row=3, column=2)
        self.reasonLabel = Label(self.dwin, text='Reason:')
        self.reasonLabel.grid(row=4, column=0)
        self.reason = Entry(self.dwin)
        self.reason.grid(row=4, column=1)
        self.okButton = Button(self.dwin, text='OK', command=self.processNewInvalidation)
        self.okButton.grid(row=5, column=0)
        self.cancelButton = Button(self.dwin, text='Cancel', command=self.closeInvalidateDialog)
        self.cancelButton.grid(row=5, column=1)
        return

    def closeInvalidateDialog(self):
        self.dwin.destroy()
        return

    def processNewInvalidation(self):
        l = self.selectedLumin.get()

        eofRunNumber = 9999999 # just use a number greater than any real run
        startText = self.startAt.get()
        endText = self.endAt.get()

        # Get and validate input
        if (startText == '-1'):
            startRun = -1
            startLS = -1
            startText = "start of fill"
        else:
            startRunLS = startText.split(':')
            if (len(startRunLS) != 2):
                tkMessageBox.showerror("Bad input", "Starting run:LS should be in the form XXXXXX:YYY")
                return
            startRun = int(startRunLS[0])
            startLS = int(startRunLS[1])

        if (endText == '-1'):
            endRun = eofRunNumber
            endLS = 99999
            endText = "end of fill"
        else:
            endRunLS = endText.split(':')
            if (len(endRunLS) != 2):
                tkMessageBox.showerror("Bad input", "Ending run:LS should be in the form XXXXXX:YYY")
                return
            endRun = int(endRunLS[0])
            endLS = int(endRunLS[1])

        reason = self.reason.get()

        if startRun != -1 and startRun not in recordedLumiSections:
            tkMessageBox.showerror("Bad input", "Start run "+str(startRun)+" not in this fill!")
            return
        if endRun != eofRunNumber and endRun not in recordedLumiSections:
            tkMessageBox.showerror("Bad input", "End run "+str(endRun)+" not in this fill!")
            return
        if startRun != -1 and startLS not in recordedLumiSections[startRun]:
            tkMessageBox.showerror("Bad input", "Start LS "+str(startLS)+" not in run "+str(startRun)+"!")
            return
        if endRun != eofRunNumber and endLS not in recordedLumiSections[endRun]:
            tkMessageBox.showerror("Bad input", "End LS "+str(endLS)+" not in run "+str(endRun)+"!")
            return
        if (startRun > endRun):
            tkMessageBox.showerror("Bad input", "Start run is after end run!")
            return
        if (startRun == endRun and startLS > endLS):
            tkMessageBox.showerror("Bad input", "Start LS is after end LS!")
            return
        if (len(reason) == 0):
            tkMessageBox.showerror("Bad input", "Please enter a reason for invalidating this section!")
            return

        # Phew, the input is valid. Now actually invalidate these lumisections!
        # There's probably a more clever way to do this than by checking every single LS but
        # this is at least simple and clear.
        for r in sorted(recordedLumiSections.keys()):
            if (r < startRun or r > endRun):
                continue
            for ls in sorted(recordedLumiSections[r].keys()):
                if (r == startRun and ls < startLS):
                    continue
                if (r == endRun and ls > endLS):
                    continue
                if not l in recordedLumiSections[r][ls]:
                    continue
                recordedLumiSections[r][ls].remove(l)

        log = l+" "+startText+" to "+endText+"; reason: "+reason+"\n"
        invalList.config(state=NORMAL)
        invalList.insert(END, log)
        invalList.config(state=DISABLED)
        logObject = {'luminometer': l, 'beginAt': self.startAt.get(), 'endAt': self.endAt.get(), 'reason': reason}
        invalidatedLumiSections.append(logObject)
        emailText = "fill "+str(fillNumber)+": "+l+" invalidated from "+startText+" to "+endText+"; reason: "+reason
        emailInformation[emailTargets[l]].append(emailText)
        
        self.dwin.destroy()
        return

# Class for name entry dialog. I'm a little surprised that there isn't a standard
# dialog type for a simple text entry, but apparently there isn't, so here we are.

class NameDialog:
    def __init__(self, parent):
        self.dwin = Toplevel(parent)
        self.dwin.title('Enter user name')
        self.titleLabel = Label(self.dwin, text='Please enter your name:')
        self.titleLabel.grid(row=0, column=0)
        self.nameEntry = Entry(self.dwin)
        self.nameEntry.grid(row=1, column=0)
        self.okButton = Button(self.dwin, text='OK', command=self.processName)
        self.okButton.grid(row=2, column=0)
        return

    def processName(self):
        self.result = self.nameEntry.get()
        if len(self.result) == 0:
            tkMessageBox.showerror("Bad input", "Please enter a name!")
            return
        self.dwin.destroy()
        return

# Code for the various buttons in the main interface window

def doInvalidateDialog():
    d = InvalidateDialog(root)
    root.wait_window(d.dwin)
    return

def displayPlot():
    print "One second, creating fill summary plot..."
    cmd = "python "+lumiValidatePath+" -f "+str(fillNumber)+" --type "+" ".join(luminometers)+" &"
    os.system(cmd)
    return

# Code for implementing the up/down buttons to change the luminometer
# priority

def priorityUp():
    changePriority(-1)
    return

def priorityDown():
    changePriority(1)
    return

def changePriority(delta):
    if len(priorityList.curselection()) == 0:
        return # nothing was selected!
    sel = int(priorityList.curselection()[0])
    if (sel + delta < 0):
        # can't move off top of list
        return
    if (sel + delta >= len(lumiPriority)):
        # can't move off bottom of list
        return
    # everything is ok, make the swap
    temp = lumiPriority[sel+delta]
    lumiPriority[sel+delta] = lumiPriority[sel]
    lumiPriority[sel] = temp
    # and refill the list boxes
    priorityList.delete(0, END)
    datatagList.delete(0, END)
    for l in lumiPriority:
        priorityList.insert(END, l)
        datatagList.insert(END, datatags[l])
    # leave the selected one selected so we can move it some more
    priorityList.selection_set(sel+delta)
    return

def exitWithoutSave():
    msg = "Do you really want to exit without saving?"
    if len(completedFills) > 0:
        msg += " (Note: fills that you have already completed have already been saved.)"
    if tkMessageBox.askyesno("Are you sure?", msg):
        if (len(completedFills) > 0):
            sendEmails()
        os.unlink(lockFileName)
        sys.exit(0)
    return

def sendEmails():
    emailSender = getpass.getuser()+"@"+socket.gethostname()
    readableFillList = ", ".join(str(f) for f in completedFills)
    suffix = "" if len(completedFills) == 1 else "s"
    for l in emailRecipients:
        emailSubject = "Fill validation results for fill"+suffix+" "+readableFillList
        emailBody = "Hello,\n\nThis is an automated email to let you know that the fill validation was performed for the following fill"+suffix+" by "+userName+":\n"
        emailBody += readableFillList
        if len(emailInformation[l])==0:
            emailBody += "\n\nNo issues were reported with "+l+" for "+("this fill" if len(completedFills) == 1 else "these fills")+"."
        else:
            emailBody += "\n\nThe following issues were reported for "+l+":\n\n"
            emailBody += "\n".join(emailInformation[l])
        emailBody += "\n\nThanks,\nthe fill validation tool"

        # Prep and send the email.
        msg = MIMEText(emailBody)
        msg['Subject'] = emailSubject
        msg['From'] = emailSender
        msg['To'] = ",".join(emailRecipients[l])
        s = smtplib.SMTP('localhost')
        s.sendmail(emailSender, emailRecipients[l], msg.as_string())

# Helper routine to get the valid lumisections for a given luminometer by calling brilcalc.
# This is an adaption of bestLumi.py which stores the output in the giant dictionary defined below.

def getValidSections(fillNumber, l):
    print "Please wait, getting valid lumisections for "+l
    tempFileName="temp_"+l+".csv"
    os.system('brilcalc lumi -f '+str(fillNumber)+' --type '+l+' -b "STABLE BEAMS" --byls -o '+tempFileName)
    with open(tempFileName) as csv_input:
        reader = csv.reader(csv_input, delimiter=',')
        for row in reader:
            if row[0][0] == '#':
                continue
            runfill=row[0].split(':')
            run=int(runfill[0])
            fill=int(runfill[1])
            lsnums=row[1].split(':')
            ls=int(lsnums[0])
            thisdet=row[8]
            # Sanity checks! If these ever actually appear I will be -very- surprised
            if (fill != fillNumber):
                print "WARNING: Output from brilcalc didn't match expected fill"
            if (thisdet.lower() != l):
                print "WARNING: Output from brilcalc didn't contain expected detector"
            # Stuff it in the dictionary!
            if not run in recordedLumiSections:
               recordedLumiSections[run] = {}
            if ls in recordedLumiSections[run]:
                recordedLumiSections[run][ls].add(l)
            else:
                recordedLumiSections[run][ls] = set([l])

    os.unlink(tempFileName)
    return

# Why do we bother with getting the beam currents? Here's why: sometimes the STABLE BEAMS flag is not cleared until several
# lumisections after the fill actually ends (especially if the beam dump is unprogrammed). These lumisections are obviously
# not actually useful and should be excluded. Since BCM1F is tied to the beam currents, it will also stop publishing when the
# beam dump actually happens, so we may get spurious warnings about bcm1f not present if we do get these extra lumisections.
# So...we look for cases where a) the beam currents are much lower (I use a factor of 50, although in practice it looks like
# it's closer to 1e4) and b) BCM1F is not present, and drop those.
def trimEndFill():
    # reverse sort to start at end of fill
    for r in sorted(recordedLumiSections.keys(), reverse=True):
        if r not in beamCurrents:
            # hmm, not sure what happened. in this case let's just err on the side of keeping everything
            print "Couldn't find beam current data for run "+str(r)+"; will skip end-of-fill check"
            return
        for ls in sorted(recordedLumiSections[r].keys(), reverse=True):
            if ls not in beamCurrents[r]:
                print "Couldn't find beam current data for run:LS "+str(r)+":"+str(ls)+"; will skip end-of-fill-check"
            if beamCurrents[r][ls]/startBeamCurrent > 0.02:
                return
            if "bcm1f" in recordedLumiSections[r][ls]:
                return

            # This meets the condition for a post-beam dump LS, so go ahead and get rid of it.
            del recordedLumiSections[r][ls]
    return

# Unfortunately json.dump only supports two types of formatting:
# none at all, or every single list element/dictionary on its own
# line, both of which are really difficult to read. So instead we
# do our own formatting by iterating over the list, using json.dumps
# to format each list element properly, and then formatting the final
# list ourselves. This is a little more work but at least it produces
# somewhat more readable output.

def writeFormattedJSON(obj, fp, sortKeys):
    outputLines = []
    for i in obj:
        outputLines.append(json.dumps(i, sort_keys=sortKeys))
    fp.write("[\n")
    fp.write(",\n".join(outputLines))
    fp.write("\n]\n")

# This takes the output for a single fill and writes it out to the JSON files.

def produceOutput():
    # 1) Update log JSON with information for this fill.
    logObject = {'fill': fillNumber, 'validated_by': userName, 'general_comments': commentsEntry.get(1.0, END),
                 'missing_lumisections': missingLumiSections, 'invalidated_lumisections': invalidatedLumiSections}
    parsedLogData.append(logObject)
    with open(logFileName, 'w') as jsonOutput:
        writeFormattedJSON(parsedLogData, jsonOutput, True)

    # 2) Next, do bestlumi. This is the most complicated...
    with open(bestLumiFileName, 'r') as bestLumiFile:
        parsedBestLumiData = json.load(bestLumiFile)

    lastLumin = ""
    lastRun = -1
    startLS = -1
    lastLS = -1
    for r in sorted(recordedLumiSections.keys()):
        for ls in sorted(recordedLumiSections[r].keys()):
            # Find the highest-priority luminometer actually present for this LS.
            for l in lumiPriority:
                if l in recordedLumiSections[r][ls]:
                    selLumin = l
                    break
            # If we've changed the luminometer or run, start a new record and save the preceding one.
            # The last case shouldn't happen unless we have a discontinuity in ALL luminometers,
            # but we should still do the right thing in this case.
            if ((selLumin != lastLumin and lastLumin != "") or
                (r != lastRun and lastRun != -1) or
                (ls != lastLS + 1 and lastLS != -1)):
                jsonRecord = [datatags[lastLumin], {str(lastRun): [[startLS, lastLS]]}]
                parsedBestLumiData.append(jsonRecord)
                startLS = ls
            lastLumin = selLumin
            lastRun = r
            lastLS = ls
            if startLS == -1:
                startLS = ls
    # Don't forget the end!
    jsonRecord = [datatags[lastLumin], {str(lastRun): [[startLS, lastLS]]}]
    parsedBestLumiData.append(jsonRecord)

    with open(bestLumiFileName, 'w') as bestLumiFile:
        writeFormattedJSON(parsedBestLumiData, bestLumiFile, False)

    # Now the individual luminometers. This is similar to the above but of course without
    # the fallback if a luminometer is missing.
    for l in luminometers:
        lumiJSONFileName = lumiJSONFileNamePattern % l
        with open(lumiJSONFileName, 'r') as lumiJSONFile:
            parsedLumiJSONData = json.load(lumiJSONFile)

        lastRun = -1
        startLS = -1
        lastLS = -1
        for r in sorted(recordedLumiSections.keys()):
            for ls in sorted(recordedLumiSections[r].keys()):
                # Don't write out this lumi section if this luminometer isn't in it!
                if not l in recordedLumiSections[r][ls]:
                    continue
                # If new run, or discontinuous LS range, print out the previous line
                if ((r != lastRun and lastRun != -1) or
                    (ls != lastLS + 1 and lastLS != -1)):
                    jsonRecord = [datatags[l], {str(lastRun): [[startLS, lastLS]]}]
                    parsedLumiJSONData.append(jsonRecord)
                    startLS = ls
                lastRun = r
                lastLS = ls
                if startLS == -1:
                    startLS = ls
        # Don't forget the end! HOWEVER if the detector was out for the whole fill then
        # do forget the end.
        if (lastRun != -1):
            jsonRecord = [datatags[l], {str(lastRun): [[startLS, lastLS]]}]
            parsedLumiJSONData.append(jsonRecord)

        with open(lumiJSONFileName, 'w') as lumiJSONFile:
            writeFormattedJSON(parsedLumiJSONData, lumiJSONFile, False)

    print "Finished writing output for fill "+str(fillNumber)
    # Mark this fill as finished properly so we will proceed to the next one.
    global currentFillSaved
    currentFillSaved = True
    root.destroy()
    return

#### Main program begins here

# A quick overview of the various ways we can leave the program and what happens in each case:
# 1) User completes all the fills. In this case the automatic emails and git commit are performed
#    after the end of the main loop.
# 2) User completes some fills and then uses the "exit without saving" button to leave. In this case
#    the automatic emails and git commit are performed in exitWithoutSave for the completed fills and
#    everything is discarded for the current fill. If no fills were completed, then the email/git commit
#    step is skipped, for obvious reasons.
# 3) User exits the program by closing the main window, or is otherwise unexpectedly terminated (e.g.
#    if the connection is dropped). In this case the current status is saved in the JSON save file. The
#    emails and git commit are NOT performed until the file is picked up and finished.

root = Tk()

# Very first step: check to see if a lock file is in existence, indicating that someone else
# is running. If so throw an error. Otherwise, create the lock file.

if os.path.exists(lockFileName):
    tkMessageBox.showerror("In use", "It looks like someone is already running this application and it has been locked to avoid conflicts. If you want to override this, remove the lock file "+lockFileName+" and try again.")
    sys.exit(1)
else:
    open(lockFileName, 'a').close()

# First read in the validation log so we can see what the last fill validated was.
logFile = open(logFileName, 'r')
parsedLogData = json.load(logFile)
# In principle the most recent fill should be the last entry -- but let's protect ourselves against
# strange things happening and just go over the whole thing
lastFill = -1
for f in parsedLogData:
    if int(f['fill']) > lastFill:
        lastFill = int(f['fill'])

# First get the list of new fills.
fillList = eval(os.popen("python "+getRecentFillPath+" -p "+dbAuthFileName+" -f "+str(lastFill)).read())
nfills = len(fillList)

if len(fillList) == 0:
    tkMessageBox.showinfo("Nothing to do!", "It looks like there are no new fills to validate. Thanks for checking!")
    os.unlink(lockFileName)
    sys.exit(0)

tkMessageBox.showinfo("Fills to validate", "It looks like there "+("is " if nfills == 1 else "are ")+str(nfills)+" new fill"+
                      ("" if nfills == 1 else "s")+" to validate:\n"+"\n".join(str(f) for f in fillList))

# Get the user's name.
userName=""
d = NameDialog(root)
root.wait_window(d.dwin)
userName = d.result

completedFills = []
currentFillSaved = False

# Information to email the user. This goes outside the fill loop because we just want to send one
# email (per subdetector) for all of the fills that get validated in this pass.
emailInformation = {}
for l in emailRecipients:
    emailInformation[l] = []

# Now, loop over each fill and do the validation for each.
for fillNumber in fillList:
    # This is a two-dimensional dictionary with keys: run number and lumisection number.
    # The value is a set of the luminometers that are present for that lumisection.
    recordedLumiSections = {}
    # This is an array of strings containing information on the invalidated lumi sections.
    invalidatedLumiSections = []
    # This is an array of objects containing information on the missing lumi sections.
    missingLumiSections = []
    # This is a dictionary like recordedLumiSections containing the beam currents.
    beamCurrents = {}

    # 1) Get the list of lumi sections recorded for each luminometer and the beam currents.

    print "Getting data for fill "+str(fillNumber)+"..."
    for l in luminometers:
        getValidSections(fillNumber, l)
    
    # See if we actually got any data for this fill.
    if len(recordedLumiSections) == 0:
        tkMessageBox.showwarning("No data for fill", "Note: no data with STABLE BEAMS was found for fill "+str(fillNumber)+" in the luminosity DB. Perhaps this fill never reached STABLE BEAMS. Otherwise, please contact an expert.")
        # Do log it though!
        logObject = {'fill': fillNumber, 'validated_by': userName, 'general_comments': 'No data in lumiDB for this fill',
                     'missing_lumisections': [], 'invalidated_lumisections': []}
        parsedLogData.append(logObject)
        with open(logFileName, 'w') as jsonOutput:
            writeFormattedJSON(parsedLogData, jsonOutput, True)

        # Mark as finished and move onto next fill.
        completedFills.append(fillNumber)
        continue

    # Get beam currents so we can clean stray lumisections at the end.
    print "Please wait, getting beam currents"
    os.system('brilcalc beam -f '+str(fillNumber)+' -b "STABLE BEAMS" -o temp_beam.csv')
    startBeamCurrent=-1
    with open('temp_beam.csv') as csv_input:
        reader = csv.reader(csv_input, delimiter=',')
        for row in reader:
            if row[0][0] == '#':
                continue
            run=int(row[1])
            ls=int(row[2])
            beam1=float(row[5])
            beam2=float(row[6])
            if run not in beamCurrents:
                beamCurrents[run] = {}
            beamCurrents[run][ls] = (beam1+beam2)
            if (startBeamCurrent == -1):
                startBeamCurrent = (beam1+beam2) # save this as a reference
    os.unlink('temp_beam.csv')

    # Clean extra lumisections after the beam dump.
    trimEndFill()

    # 2) Display the fill validation plot.

    displayPlot()

    # 3) Display the main GUI and let the user make their changes.
    titleLabel = Label(root, text='Fill validation for fill '+str(fillNumber), font=('Arial', 24))
    titleLabel.grid(row=0, column=0)
    userLabel = Label(root, text='User: '+userName)
    userLabel.grid(row=1, column=0)
    redispButton = Button(root, text='Redisplay validation plot', command=displayPlot)
    invalButton = Button(root, text='Invalidate lumisection(s)', command=doInvalidateDialog)
    finishNextButton = Button(root, text='Finish this fill and continue', command=produceOutput)
    finishQuitButton = Button(root, text='Exit without saving', command=exitWithoutSave)
    redispButton.grid(row=2, column=0)
    invalButton.grid(row=3, column=0)
    finishNextButton.grid(row=4, column=0)
    finishQuitButton.grid(row=5, column=0)
    commentsLabel = Label(root, text='General comments on this fill')
    commentsLabel.grid(row=6, column=0)
    commentsEntry = Text(root, width=60, height=4)
    commentsEntry.grid(row=7, column=0)
    
    priorityLabel = Label(root, text='Priority')
    priorityLabel.grid(row=0, column=1)
    priorityList = Listbox(root, selectmode=SINGLE)
    priorityList.grid(row=1, column=1, rowspan=7)
    
    priUpButton = Button(root, text=unichr(8593), command=priorityUp)
    priUpButton.grid(row=2, column=2, sticky='W')
    priDownButton = Button(root, text=unichr(8595), command=priorityDown)
    priDownButton.grid(row=3, column=2, sticky='W')
    
    datatagLabel = Label(root, text='Datatags')
    datatagLabel.grid(row=0, column=3)
    datatagList = Listbox(root)
    datatagList.grid(row=1, column=3, rowspan=7)
    
    for l in lumiPriority:
        priorityList.insert(END, l)
        datatagList.insert(END, datatags[l])
        
    missingLabel = Label(root, text='Missing lumisections')
    missingLabel.grid(row=10, column=0)
    missingList = Text(root, width=60, height=15)
    missingList.grid(row=11, column=0)
    
    invalLabel = Label(root, text='Invalidated lumisections')
    invalLabel.grid(row=10, column=1, columnspan=3)
    invalList = Text(root, width=60, height=15)
    invalList.grid(row=11, column=1, columnspan=3)

    # 4) Look for missing lumisections and populate the missing lumisections field appropriately.
    
    for l in luminometers:
        luminometerPresent=1
        startSection=""
        lastSection=""
        for r in sorted(recordedLumiSections.keys()):
            for ls in sorted(recordedLumiSections[r].keys()):
                if (luminometerPresent == 1 and l not in recordedLumiSections[r][ls]):
                    # Start of new section where this luminometer is not present
                    startSection=str(r)+":"+str(ls)
                    luminometerPresent = 0
                if (luminometerPresent == 0 and l in recordedLumiSections[r][ls]):
                    # End of section where this luminometer is not present
                    log = l+" "+startSection+" to "+lastSection+"\n"
                    missingList.insert(END, log)
                    logObject = {'luminometer': l, 'beginAt': startSection, 'endAt': lastSection}
                    missingLumiSections.append(logObject)
                    emailText = "fill "+str(fillNumber)+": "+l+" missing from "+startSection+" to "+lastSection
                    emailInformation[emailTargets[l]].append(emailText)
                    luminometerPresent = 1
                lastSection=str(r)+":"+str(ls)
        # Check to see if we reached the end of fill without this luminometer coming back. If so, go through the same
        # drill...
        if (luminometerPresent == 0):
            log = l+" "+startSection+" to "+lastSection+"\n"
            missingList.insert(END, log)
            logObject = {'luminometer': l, 'beginAt': startSection, 'endAt': lastSection}
            missingLumiSections.append(logObject)
            emailText = "fill "+str(fillNumber)+": "+l+" missing from "+startSection+" to "+lastSection
            emailInformation[emailTargets[l]].append(emailText)


    # Disable missing and invalidated fields
    missingList.config(state=DISABLED)
    invalList.config(state=DISABLED)

    root.mainloop()

    # If we made it here, then either (a) we saved the data from the fill, in which case we can
    # just happily proceed to the next one, or (b) the user closed the main window, in which case
    # we should just exit semi-gracefully.
    if not currentFillSaved:
        print "Application closed."
        os.unlink(lockFileName)
        sys.exit(1)

    # OK, set up for the next fill.
    completedFills.append(fillNumber)
    currentFillSaved = False
    root = Tk()

print "Validation complete. Thanks!"
sendEmails()
os.unlink(lockFileName)
