from parsing.fields import *
from parsing.parser import *
from parsing.writer import *
from parsing.track import *
from util import *

from shutil import copyfileobj
from tkinter import *
from tkinter import ttk, filedialog

import os
import re

class Gui:

    def __init__(self):
        self.state = {'fields':{},'changes':{}}
        self.parseWems()
        self.load()

    def parseWems(self):
        wems = {}
        trackNameToId = {}
        mainTracks = []
        with open(getResourcePath(os.path.join('resources','wems.csv')), 'r') as data:
            for line in data:
                splits = line.split(',')
                trackId = int(splits[1])
                trackName = splits[4]
                trackGroup = splits[6]
                isMain = int(splits[7])
                if wems.get(trackGroup) is None:
                    wems[trackGroup] = []
                wems[trackGroup].append(trackName)
                trackNameToId[trackName] = trackId
                if isMain == 1:
                    mainTracks.append(trackId)

        self.state['wems'] = wems
        self.state['idmap'] = trackNameToId
        self.state['maintracks'] = mainTracks
        self.state['tracks'] = {}

    def load(self):
        self.root = Tk()
        self.root.geometry('1200x720')

        # self.root.tk.call('lappend', 'auto_path', 'resources/themes')
        # #self.root.tk.call('package', 'require', 'yaru')
        # self.root.tk.call('source', 'resources/themes/yaru/yaru.tcl')
        # self.style = ttk.Style()
        # self.style.theme_use('yaru')

        headerFrame = ttk.Frame(self.root, height=10)
        headerFrame.pack(side=TOP, fill=X, expand=False)

        loadButton = ttk.Button(headerFrame, text='Open', command=self.openNbnk)
        loadButton.pack(side=LEFT)

        saveButton = ttk.Button(headerFrame, text='Save As')
        saveButton.bind("<ButtonRelease-1>", self.handleSave)
        saveButton.pack(side=LEFT)

        exportButton = ttk.Button(headerFrame, text='Export JSON')
        exportButton.pack(side=LEFT)

        resetButton = ttk.Button(headerFrame, text='Reset Track')
        resetButton.pack(side=LEFT)

        mainFrame = ttk.Frame(self.root)
        mainFrame.pack(side=TOP, fill=BOTH, expand=True, padx=10, pady=10)

        selectFrame = ttk.Frame(mainFrame)
        selectFrame.pack(side=LEFT, fill=Y, expand=False)

        ttk.Label(selectFrame, text='Track Groups:').pack(side=TOP, anchor=NW)

        groupFrame = ttk.Frame(selectFrame)
        groupFrame.pack(side=TOP, fill=X, expand=False)

        groupBox = Listbox(groupFrame, width=50, height=15)
        groupBox.bind("<ButtonRelease-1>", self.handleGroup)
        groupBox.pack(side=LEFT, expand=False)
        groupScroller = Scrollbar(groupFrame, orient=VERTICAL)
        groupBox.config(yscrollcommand=groupScroller.set)
        groupScroller.config(command=groupBox.yview)
        groupScroller.pack(side=RIGHT, fill=Y)

        ttk.Label(selectFrame, text='Tracklist:').pack(side=TOP, anchor=NW)

        tracklistFrame = ttk.Frame(selectFrame)
        tracklistFrame.pack(side=TOP, fill=BOTH, expand=True)

        trackBox = Listbox(tracklistFrame, width=50, height=75)
        trackBox.bind("<ButtonRelease-1>", self.handleTrack)
        trackBox.pack(side=LEFT, fill=Y, expand=True)
        trackScroller = Scrollbar(tracklistFrame, orient='vertical')
        trackBox.config(yscrollcommand=trackScroller.set)
        trackScroller.config(command=trackBox.yview)
        trackScroller.pack(side=RIGHT, fill=Y)

        detailFrame = ttk.Frame(mainFrame)
        detailFrame.pack(side=RIGHT, padx=5)

        self.groups = groupBox
        self.tracks = trackBox
        self.details = detailFrame

    def openNbnk(self):
        path = filedialog.askopenfilename(filetypes=[("Wwise Soundbanks","*.nbnk")])
        print(path)
        if not path:
            return
        bank = parse(path)
        if not bank:
            return
        ## clear existing state ##
        self.clearState()
        ## load the bank ##
        self.path = path
        self.bank = bank
        print(f'Bank loaded with {len(bank.getTracks())} tracks')
        self.loadGroups()

    def loadGroups(self):
        sortedGroups = list(self.state['wems'].keys())
        sortedGroups.sort()
        for key in sortedGroups:
            self.groups.insert(END, key)

    def handleGroup(self, event):
        selection = event.widget.curselection()
        if not selection:
            return
        value = event.widget.get(selection[0])
        self.state['group'] = value
        tracks = self.state['wems'].get(value)
        tracks.sort()
        self.tracks.delete(0, END)
        for track in tracks:
            self.tracks.insert(END, track)

    def handleTrack(self, event):
        selection = event.widget.curselection()
        if not selection:
            return
        self.checkForChanges()
        self.clearDetails()
        value = event.widget.get(selection[0])
        self.state['trackname'] = value
        trackId = self.state['idmap'][value]
        trackData = self.bank.getTrackData(trackId)
        isMain = trackId in self.state['maintracks']

        changedTrack = self.state['changes'].get(f'{trackId}')
        if not changedTrack is None:
            # load from changes
            self.loadTrackDataFromChange(changedTrack, isMain)
        self.loadTrackData(trackData, trackId, isMain)

        self.details.pack()

    def loadTrackDataFromChange(self, track, isMain):
        trackFrame = self.createTrackEntries(track, track.lengthVar)
        for section in track.sections:
            clipFrame = self.createSectionEntries(section, section.durVar)
            for clip in section.playlist:
                self.createClipEntries(clip, clipFrame, clip.start, clip.end)
        self.state['tracks'][track.trackId] = track

    def loadTrackData(self, trackData, trackId, isMain):
        track = Track(trackId)
        trackLength = None
        trackFrame = None
        for sectionId, sectionData in trackData.items():
            ## finish initializing the track and frame ##
            if trackLength is None:
                trackLength = sectionData['playlist'][0][Fields.TOTAL_LENGTH][1]
                track.setLength(trackLength)
                trackFrame = self.createTrackEntries(track)
            section = self.loadSectionData(track, sectionData, sectionId, trackFrame)
            track.addSection(section)
        self.state['tracks'][trackId] = track

    def loadSectionData(self, track, sectionData, sectionId, frame):
        playlist = sectionData['playlist']
        durations = sectionData['durations']
        markers = sectionData['markers']
        section = Section(sectionId)

        durationOffsets = [td[0] for td in durations]
        durationVal = durations[0][1]
        section.setDuration(durationVal)
        section.addDurationOffsets(durationOffsets)

        clipFrame = self.createSectionEntries(section)
        for clipData in playlist:
            clip = self.loadClipData(track, clipData, clipFrame)
            section.addClip(clip)

        return section

    def loadClipData(self, track, clipData, frame):
        startNegOffset = clipData[Fields.PLAY_AT][0]
        startNegVal = clipData[Fields.PLAY_AT][1]

        startPosOffset = clipData[Fields.BEGIN_OFFSET][0]
        startPosVal = clipData[Fields.BEGIN_OFFSET][1]

        remainOffset = clipData[Fields.REMAINING][0]
        remainVal = clipData[Fields.REMAINING][1]

        lengthOffset = clipData[Fields.TOTAL_LENGTH][0]

        clip = Clip(startNegVal, startPosVal, remainVal, track)
        clip.addPlayOffset(startNegOffset)
        clip.addBeginOffset(startPosOffset)
        clip.addRemainOffset(remainOffset)
        track.addLengthOffset(lengthOffset)

        self.createClipEntries(clip, frame)
        return clip

    def createTrackEntries(self, track, lengthVar=None):
        if lengthVar is None:
            lengthVar = DoubleVar(value=track.length)
            track.setVars(lengthVar)
        frame = ttk.Frame(self.details)
        frame.pack(side=TOP, fill=BOTH, expand=True)
        ttk.Label(frame, text=self.state['trackname']).pack(side=LEFT)
        ttk.Label(frame, text='Track Length:').pack(side=LEFT)
        ttk.Entry(frame, textvariable=lengthVar, width=20).pack(side=LEFT)
        ttk.Separator(self.details).pack(side=TOP, fill=X, pady=2)
        return frame

    def createSectionEntries(self, section, durationVar=None):
        if durationVar is None:
            durationVar = DoubleVar(value=section.duration)
            section.setVars(durationVar)
        frame = ttk.Frame(self.details)
        frame.pack(side=TOP, fill=BOTH, expand=True)
        sectionFrame = ttk.Frame(frame)
        sectionFrame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10)
        ttk.Label(sectionFrame, text='Section Length:').pack(side=LEFT)
        ttk.Entry(sectionFrame, textvariable=durationVar, width=20).pack(side=LEFT)
        clipFrame = ttk.Frame(frame)
        clipFrame.pack(side=RIGHT, fill=BOTH, expand=True)
        ttk.Separator(self.details).pack(side=TOP, fill=X, pady=2)
        return clipFrame

    def createClipEntries(self, clip, parentFrame, startVar=None, endVar=None):
        if startVar is None or endVar is None:
            startVar = DoubleVar(value=clip.getStart())
            endVar = DoubleVar(value=clip.getEnd())
            clip.setVars(startVar, endVar)
        frame = ttk.Frame(parentFrame)
        frame.pack(side=TOP, fill=X, expand=True)
        ttk.Label(frame, text='Start:').pack(side=LEFT)
        ttk.Entry(frame, textvariable=startVar, width=20).pack(side=LEFT)
        ttk.Label(frame, text='End:').pack(side=LEFT)
        ttk.Entry(frame, textvariable=endVar, width=20).pack(side=LEFT)

    ## Iterate over all currently drawn track fields and store any changes ##
    def checkForChanges(self):
        ## mark track as changed as soon as we find a value that has changed ##
        ## this is also where we update the track/section/clip objects with the new var values ##
        for trackId, track in self.state['tracks'].items():
            curLen = track.getCurLength()
            if curLen != track.length:
                track.applyChanges()
                self.state['changes'][f'{trackId}'] = track
                continue
            for section in track.sections:
                curDur = section.getCurDuration()
                if curDur != section.duration:
                    track.applyChanges()
                    self.state['changes'][f'{trackId}'] = track
                    continue
                for clip in section.playlist:
                    curStart = clip.getCurStart()
                    curEnd = clip.getCurEnd()
                    if curStart != clip.getStart() or curEnd != clip.getEnd():
                        track.applyChanges()
                        self.state['changes'][f'{trackId}'] = track
                        continue

    ## Write all changes to a new file ##
    def handleSave(self, event):
        self.checkForChanges()
        ## abort if no changes ##
        if len(self.state['changes']) == 0:
            return
        ## otherwise copy original nbnk to new file ##
        ## then apply all changes at the corresponding offsets in new file ##
        newpath = filedialog.asksaveasfilename(defaultextension=".nbnk")
        if not newpath:
            return
        with open(self.path, 'rb') as oldfile:
            with open(newpath, 'wb+') as newfile:
                try:
                    copyfileobj(oldfile, newfile)
                    writer = Writer(newfile)
                    for trackId, track in self.state['changes'].items():
                        track.writeToFile(writer)
                except IOError:
                    print("failed to write new file")

    def clearState(self):
        self.state['changes'].clear()
        self.groups.delete(0, END)
        self.tracks.delete(0, END)
        self.clearDetails()

    def clearDetails(self):
        self.state['tracks'].clear()
        for widget in self.details.winfo_children():
            widget.destroy()
        self.details.pack_forget()

    def validateDouble(self, value):
        return re.match(r"(\-)?\d+(.\d+)?$", value) is not None

    def handleEntry(self, event):
        if 'invalid' in event.widget.state():
            event.widget.configure(fg = 'red')
        else:
            event.widget.configure(fg = 'black')

    def start(self):
        self.root.mainloop()
