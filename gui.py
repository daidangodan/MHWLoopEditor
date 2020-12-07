from parsing.fields import *
from parsing.parser import *
from parsing.writer import *

from tkinter import *
from tkinter import ttk, filedialog

import re

class Gui:

    def __init__(self):
        self.state = {'fields':[],'changes':{}}
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

        mainFrame = ttk.Frame(self.root)
        mainFrame.pack(side=TOP, fill=BOTH, expand=True, padx=10, pady=10)

        selectFrame = ttk.Frame(mainFrame)
        selectFrame.pack(side=LEFT, fill=Y, expand=False)

        groupBox = Listbox(selectFrame, width=50, height=15)
        groupBox.bind("<ButtonRelease-1>", self.handleGroup)
        groupBox.pack(side=TOP, fill=X, expand=True)
        # groupScroller = Scrollbar(groupBox, orient='vertical')
        # groupBox.config(yscrollcommand=groupScroller.set)
        # groupScroller.config(command=groupBox.yview)
        # groupScroller.pack(side=RIGHT, fill=Y)

        trackBox = Listbox(selectFrame, width=50, height=75)
        trackBox.bind("<ButtonRelease-1>", self.handleTrack)
        trackBox.pack(side=TOP, fill=BOTH, expand=True)
        # trackScroller = Scrollbar(trackBox, orient='vertical')
        # trackBox.config(yscrollcommand=trackScroller.set)
        # trackScroller.config(command=trackBox.yview)
        # trackScroller.pack(side=RIGHT, fill=Y)

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
        self.clearFrame(self.details)
        for track in tracks:
            self.tracks.insert(END, track)

    def handleTrack(self, event):
        selection = event.widget.curselection()
        if not selection:
            return
        self.clearFrame(self.details)
        value = event.widget.get(selection[0])
        self.state['track'] = value
        trackId = self.state['idmap'][value]
        trackDatas = self.bank.getTrackData(trackId)
        isMain = trackId in self.state['maintracks']
        for sectionId in trackDatas:
            self.loadTrackData(trackDatas[sectionId], trackId, sectionId, isMain)
        self.details.pack()

    def loadTrackData(self, trackData, trackId, sectionId, isMain):
        trackPlaylist = trackData['playlist']
        trackDurations = trackData['durations']
        trackMarkers = trackData['markers']
        for idx, bundle in enumerate(trackPlaylist):
            subFrame = ttk.Frame(self.details)
            subFrame.pack(side=TOP, fill=BOTH, expand=True)
            startNegOffset = bundle[Fields.PLAY_AT][0]
            startNegVal = bundle[Fields.PLAY_AT][1]
            startNegName = f'{trackId}-{sectionId}-{idx}-{Fields.PLAY_AT}'
            startPosOffset = bundle[Fields.BEGIN_OFFSET][0]
            startPosVal = bundle[Fields.BEGIN_OFFSET][1]
            startPosName = f'{trackId}-{sectionId}-{idx}-{Fields.BEGIN_OFFSET}'
            remainOffset = bundle[Fields.REMAINING][0]
            remainVal = bundle[Fields.REMAINING][1]
            remainName = f'{trackId}-{sectionId}-{idx}-{Fields.REMAINING}'
            lengthOffset = bundle[Fields.TOTAL_LENGTH][0]
            lengthVal = bundle[Fields.TOTAL_LENGTH][1]
            lengthName = f'{trackId}-{sectionId}-{idx}-{Fields.TOTAL_LENGTH}'

            ttk.Label(subFrame, text='Start (-):').pack(side=LEFT)
            self.createEntry(subFrame, startNegName, startNegVal, [startNegOffset])
            ttk.Label(subFrame, text='Start (+):').pack(side=LEFT)
            self.createEntry(subFrame, startPosName, startPosVal, [startPosOffset])
            ttk.Label(subFrame, text='Remain:').pack(side=LEFT)
            self.createEntry(subFrame, remainName, remainVal, [remainOffset])
            ttk.Label(subFrame, text='Track Length:').pack(side=LEFT)
            self.createEntry(subFrame, lengthName, lengthVal, [lengthOffset])
            ttk.Separator(self.details).pack(side=TOP, fill=X, pady=1)
        ## only add the track duration part if this is a main track ##
        if isMain:
            subFrame = ttk.Frame(self.details)
            subFrame.pack(side=TOP, fill=BOTH, expand=True)
            durationOffsets = [td[0] for td in trackDurations]
            durationVal = trackDurations[0][1]
            durationName = f'{trackId}-{sectionId}-{Fields.SECTION_LENGTH}'
            ttk.Label(subFrame, text='Section Length:').pack(side=LEFT)
            self.createEntry(subFrame, durationName, durationVal, durationOffsets)
            ttk.Separator(self.details).pack(side=TOP, fill=X, pady=2)
        return

    def createEntry(self, frame, name, value, offsets):
        var = self.state['changes'].get(name)
        if var is None:
            var = DoubleVar(value=value)
        entry = ttk.Entry(frame, textvariable=var, width=30, name=name)
        entry.pack(side=LEFT)
        self.state['fields'].append((entry, var, var.get(), offsets))

    def handleSave(self, event):
        for entry, var, original, offsets in self.state['fields']:
            curVal = float(entry.get())
            if curVal != original:
                self.state['changes'][entry.winfo_name()] = (curVal, offsets)
        newpath = filedialog.asksaveasfilename(defaultextension=".nbnk")
        print(newpath)
        if not newpath:
            return
        originalFile = open(self.path, 'rb')
        originalData = originalFile.read()
        newFile = open(newpath, 'wb+')
        newFile.write(originalData)
        originalFile.close()
        writer = Writer(newFile)
        for key in self.state['changes']:
            newValue, offsets = self.state['changes'][key]
            for offset in offsets:
                writer.writeDouble(newValue, int(offset, 16))
        newFile.close

    def clearFrame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()
        frame.pack_forget()
        self.state['fields'].clear()

    def validateDouble(self, value):
        return re.match(r"(\-)?\d+(.\d+)?$", value) is not None

    def handleEntry(self, event):
        if 'invalid' in event.widget.state():
            event.widget.configure(fg = 'red')
        else:
            event.widget.configure(fg = 'black')

    def start(self):
        self.root.mainloop()
