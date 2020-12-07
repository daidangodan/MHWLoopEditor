import struct
import fields

class Reader:

    def __init__(self, data):
        self.data = data

    def read(self, size):
        return self.data.read(size)

    def readUInt8(self):
        return struct.unpack("B", self.data.read(1))[0]

    def readUInt16(self):
        return struct.unpack("H", self.data.read(2))[0]

    def readUInt32(self):
        return struct.unpack("I", self.data.read(4))[0]

    def readDouble(self):
        return struct.unpack("d", self.data.read(8))[0]

    def readString(self, size):
        return self.data.read(size).decode()

    def readHexString(self, size):
        return self.data.read(size).hex()

    def advance(self, offset):
        self.data.seek(offset, 1)

    def getOffset(self):
        return self.data.tell()

    def readTrack(self, bank):
        chunkSize = self.readUInt32()
        ## Remember this for later ##
        endOfChunk = self.data.tell() + chunkSize
        ## Skip over unused data ##
        self.advance(5)
        numSources = self.readUInt32()
        if (numSources == 0):
            self.data.seek(endOfChunk)
            return
        self.advance(numSources * 14)
        ## Parse out the track datas and store in temporary map ##
        tempSectionData = {}
        numPlaylist = self.readUInt32()
        for i in range(numPlaylist):
            self.advance(4)
            trackId = self.readUInt32()
            if not tempSectionData.get(trackId): tempSectionData[trackId] = []
            trackInfo = {}
            trackInfo[Fields.PLAY_AT] = (self.getOffset(), self.readDouble())
            trackInfo[Fields.BEGIN_OFFSET] = (self.getOffset(), self.readDouble())
            trackInfo[Fields.REMAINING] = (self.getOffset(), self.readDouble())
            trackInfo[Fields.TOTAL_LENGTH] = (self.getOffset(), self.readDouble())
            tempSectionData[trackId].append(trackInfo)
        ## Skip over unused data ##
        self.advance(4)
        numClips = self.readUInt32()
        for j in range(numClips):
            self.advance(8)
            numPoints = self.readUInt32()
            self.advance(numPoints * 12)
        self.advance(7)
        ## SectionId is used to tie together tracks sharing common properties like duration ##
        sectionId = self.readUInt32()
        ## Update trackId to sectionId map and record track data to bank ##
        for trackId in tempSectionData:
            bank.addPlaylistForTrackSection(trackId, sectionId, tempSectionData[trackId])
            bank.updateTrackMap(key, sectionId)
        self.data.seek(endOfChunk)
        return

    def readSegment(self, bank):
        chunkSize = self.readUInt32()
        ## Remember this for later ##
        endOfChunk = self.data.tell() + chunkSize
        sectionId = self.readUInt32()
        # Skip over unused data ##
        self.advance(13)
        akProps = self.readUInt8()
        self.advance(akProps * 5)
        rangedProps = self.readUInt8()
        if (rangedProps > 0):
            print('rangedProps > 0 at: ' + str(self.data.tell()))
            self.data.seek(endOfChunk)
            return
        self.advance(8)
        numStateGroups = self.readUInt32()
        for i in range(numStateGroups):
            self.advance(5)
            numStates = self.readUInt16()
            self.advance(numStates * 8)
        numRTPC = self.readUInt16()
        if (numRTPC > 0):
            print('numRTPC > 0 at: ' + str(self.data.tell()))
            self.data.seek(endOfChunk)
            return
        #print(hex(self.data.tell()))
        numChilds = self.readUInt32()
        #print('numChilds: ' + str(numChilds))
        self.advance(numChilds * 4 + 23)
        #print(hex(self.data.tell()))
        numStingers = self.readUInt32()
        if (numStingers > 0):
            print('numStingers > 0 at: ' + str(self.data.tell()))
            self.data.seek(endOfChunk)
            return
        ## Record the two duration values for this section ##
        ## Also record the intermediate markers in case we need to update later ##
        durations = []
        markers = []
        durations.append((self.getOffset(), self.readDouble()))
        numMarkers = self.readUInt32()
        if (numMarkers > 0):
            for j in range(numMarkers):
                markerId = self.readUInt32()
                if (markerId == 1539036744):
                    durations.append((self.getOffset(), self.readDouble()))
                else:
                    markers.append((self.getOffset(), self.readDouble()))
                stringSize = self.readUInt32()
                self.advance(stringSize)

        trackIdsForSection = bank.getTracksForSection(sectionId)
        for tId in trackIdsForSection:
            bank.updateTrackSection(tId, sectionId, durations, markers)
        ## Just to be sure we are still aligned ##
        self.data.seek(endOfChunk)
        return

