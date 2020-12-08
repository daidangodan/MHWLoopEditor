from parsing.fields import *
from parsing.parser import *
from parsing.writer import *
from parsing.track import *

from shutil import copyfileobj
from tkinter import *
from tkinter import ttk, filedialog

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
        with open('resources/wems.csv', 'r') as data:
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
        self.state['sections'] = {}

    def load(self):
        self.root = Tk()
        self.root.geometry('1200x720')

        #self.root.tk.call('lappend', 'auto_path', 'themes')
        #self.root.tk.call('package', 'require', 'yaru')
        #self.root.tk.call('source', 'themes/yaru/yaru.tcl')
        #self.style = ttk.Style()
        #self.style.theme_use('yaru')

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
        self.state['track'] = value
        trackId = self.state['idmap'][value]
        trackDatas = self.bank.getTrackData(trackId)
        isMain = trackId in self.state['maintracks']
        for sectionId in trackDatas:
            changedTrack = self.state['changes'].get(f'{trackId}-{sectionId}')
            if not changedTrack is None:
                # load from changes
                self.loadTrackDataFromChange(changedTrack, sectionId, isMain)
            self.loadTrackData(trackDatas[sectionId], trackId, sectionId, isMain)
        self.details.pack()

    def loadTrackData(self, trackData, trackId, sectionId, isMain):
        trackPlaylist = trackData['playlist']
        trackDurations = trackData['durations']
        trackMarkers = trackData['markers']
        track = Track(trackId, sectionId)
        track.setLength(trackPlaylist[0][Fields.TOTAL_LENGTH][1])
        for idx, bundle in enumerate(trackPlaylist):
            startNegOffset = bundle[Fields.PLAY_AT][0]
            startNegVal = bundle[Fields.PLAY_AT][1]

            startPosOffset = bundle[Fields.BEGIN_OFFSET][0]
            startPosVal = bundle[Fields.BEGIN_OFFSET][1]

            remainOffset = bundle[Fields.REMAINING][0]
            remainVal = bundle[Fields.REMAINING][1]

            lengthOffset = bundle[Fields.TOTAL_LENGTH][0]
            lengthVal = bundle[Fields.TOTAL_LENGTH][1]

            clip = Clip(startNegVal, startPosVal, remainVal, lengthVal)
            clip.addPlayOffset(startNegOffset)
            clip.addBeginOffset(startPosOffset)
            clip.addRemainOffset(remainOffset)
            track.addLengthOffset(lengthOffset)

            self.createClipEntries(clip)
            track.addClip(clip)

            # ttk.Label(subFrame, text='Start (-):').pack(side=LEFT)
            # self.createEntry(subFrame, startNegName, startNegVal, [startNegOffset])
            # ttk.Label(subFrame, text='Start (+):').pack(side=LEFT)
            # self.createEntry(subFrame, startPosName, startPosVal, [startPosOffset])
            # ttk.Label(subFrame, text='Remain:').pack(side=LEFT)
            # self.createEntry(subFrame, remainName, remainVal, [remainOffset])
            # ttk.Label(subFrame, text='Track Length:').pack(side=LEFT)
            # self.createEntry(subFrame, lengthName, lengthVal, [lengthOffset])
            # ttk.Separator(self.details).pack(side=TOP, fill=X, pady=1)

        durationOffsets = [td[0] for td in trackDurations]
        durationVal = trackDurations[0][1]

        track.setDuration(durationVal)
        track.addDurationOffsets(durationOffsets)
        self.createTrackEntries(track)

        # ttk.Label(subFrame, text='Section Length:').pack(side=LEFT)
        # self.createEntry(subFrame, durationName, durationVal, durationOffsets)
        self.state['sections'][sectionId] = track
        return

    def loadTrackDataFromChange(self, track, sectionId, isMain):
        for clip in track.playlist:
            self.createClipEntries(clip, clip.start, clip.end)
        self.createTrackEntries(track, track.durVar, track.lengthVar)
        self.state['sections'][sectionId] = track

    def createClipEntries(self, clip, startVar=None, endVar=None):
        if startVar is None or endVar is None:
            startVar = DoubleVar(value=clip.getStart())
            endVar = DoubleVar(value=clip.getEnd())
            clip.setVars(startVar, endVar)
        frame = ttk.Frame(self.details)
        frame.pack(side=TOP, fill=BOTH, expand=True)
        ttk.Label(frame, text='Start:').pack(side=LEFT)
        ttk.Entry(frame, textvariable=startVar, width=20).pack(side=LEFT)
        ttk.Label(frame, text='End:').pack(side=LEFT)
        ttk.Entry(frame, textvariable=endVar, width=20).pack(side=LEFT)

        # self.state['fields'][startName] = (startVar, startVar.get(), clip)
        # self.state['fields'][endName] = (endVar, endVar.get(), clip)

    def createTrackEntries(self, track, durationVar=None, lengthVar=None):
        if durationVar is None or lengthVar is None:
            durationVar = DoubleVar(value=track.duration)
            lengthVar = DoubleVar(value=track.length)
            track.setVars(durationVar, lengthVar)
        frame = ttk.Frame(self.details)
        frame.pack(side=TOP, fill=BOTH, expand=True)
        ttk.Label(frame, text='Section Length:').pack(side=LEFT)
        ttk.Entry(frame, textvariable=durationVar, width=20).pack(side=LEFT)
        ttk.Label(frame, text='Track Length:').pack(side=LEFT)
        ttk.Entry(frame, textvariable=lengthVar, width=20).pack(side=LEFT)
        ttk.Separator(self.details).pack(side=TOP, fill=X, pady=2)
        
        # self.state['fields'][durationName] = (durationVar, durationVar.get(), track)
        # self.state['fields'][lengthName] = (lengthVar, lengthVar.get(), track)

    ## Iterate over all currently drawn track fields and store any changes ##
    def checkForChanges(self):
        for sectionId in self.state['sections']:
            track = self.state['sections'][sectionId]
            curDur = track.getCurDuration()
            curLen = track.getCurLength()
            ## mark track as changed as soon as we find a value that has changed ##
            ## this is also where we update the track and clip objects with the new var values ##
            if curDur != track.duration or curLen != track.length:
                track.applyChanges()
                self.state['changes'][f'{track.trackId}-{track.sectionId}'] = track
                continue
            else:
                for clip in track.playlist:
                    curStart = clip.getCurStart()
                    curEnd = clip.getCurEnd()
                    if curStart != clip.getStart() or curEnd != clip.getEnd():
                        track.applyChanges()
                        self.state['changes'][f'{track.trackId}-{track.sectionId}'] = track
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
                    for section, track in self.state['changes'].items():
                        #trackId,sectionId = tuple(section.split('-'))
                        track.writeToFile(writer)
                except IOError:
                    print("failed to write new file")

    # def handleSave(self, event):
    #     for entry, var, original, offsets in self.state['fields']:
    #         curVal = float(entry.get())
    #         if curVal != original:
    #             self.state['changes'][entry.winfo_name()] = (curVal, offsets)
    #     newpath = filedialog.asksaveasfilename(defaultextension=".nbnk")
    #     print(newpath)
    #     if not newpath:
    #         return
    #     copyfile(self.path, newpath)
    #     newFile = open(newpath, 'wb+')
    #     writer = Writer(newFile)
    #     for key in self.state['changes']:
    #         newValue, offsets = self.state['changes'][key]
    #         for offset in offsets:
    #             writer.writeDouble(newValue, int(offset, 16))
    #     newFile.close

    def clearState(self):
        self.state['changes'].clear()
        self.groups.delete(0, END)
        self.tracks.delete(0, END)
        self.clearDetails()

    def clearDetails(self):
        self.state['sections'].clear()
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
