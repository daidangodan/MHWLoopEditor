class Bank:

    def __init__(self, size, numChunks):
        self.size = size
        self.numChunks = numChunks
        self.chunks = {}
        self.sectionToTrackMap = {}

    def getOrAddTrack(self, trackId):
        if not self.chunks.get(trackId):
            self.chunks[trackId] = {'playlist': []}
        return self.chunks.get(trackId)

    def addPlaylistForTrackSection(self, trackId, sectionId, playlist):
        track = self.getOrAddTrack(trackId)
        track[sectionId]['playlist'] = playlist

    def updateTrackSection(self, trackId, sectionId, durations, markers):
        track = self.getOrAddTrack(trackId)
        track[sectionId]['durations'] = durations
        track[sectionId]['markers'] = markers

    def getTracksForSection(self, sectionId):
        return self.sectionToTrackMap.get(sectionId)

    def updatesectionToTrackMap(self, trackId, sectionId):
        if not self.sectionToTrackMap.get(sectionId): self.sectionToTrackMap[sectionId] = []
        self.sectionToTrackMap[sectionId].append(trackId)

    def getTrackData(self, trackId):
        #sectionIds = self.getSectionsForTrack(trackId)
        #trackData = {trackId:[], 'durations':[], 'markers':[]}
        return self.chunks.get(trackId)

    def updateChunk(self, chunkId, data):
        if not self.chunks.get(chunkId): self.chunks[chunkId] = {}
        for key in data:
            if self.chunks[chunkId].get(key):
                self.chunks[chunkId][key] += data[key]
            else:
                self.chunks[chunkId][key] = data[key]

    def getChunk(self, chunkId):
        return self.chunks.get(chunkId)

    def getKeys(self):
        return list(self.chunks.keys())

    def getSectionsForTrack(self, trackId):
        return self.sectionToTrackMap.get(trackId)

    def getTracks(self):
        return list(self.sectionToTrackMap.keys())

    def __str__(self):
        return "Bank: " + str(self.size) + " bytes, " + str(self.numChunks) + " items"
