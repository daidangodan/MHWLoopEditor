class Bank:

    def __init__(self, size, numtracks):
        self.size = size
        self.numtracks = numtracks
        self.tracks = {}
        self.sectionToTrackMap = {}

    def getOrAddTrack(self, trackId):
        if not self.tracks.get(trackId):
            self.tracks[trackId] = {}
        return self.tracks.get(trackId)

    def addPlaylistForTrackSection(self, trackId, sectionId, playlist):
        track = self.getOrAddTrack(trackId)
        if not track.get(sectionId):
            track[sectionId] = {}
        track[sectionId]['playlist'] = playlist

    def updateTrackSection(self, trackId, sectionId, durations, markers):
        track = self.getOrAddTrack(trackId)
        track[sectionId]['durations'] = durations
        track[sectionId]['markers'] = markers

    def getTracksForSection(self, sectionId):
        if not self.sectionToTrackMap.get(sectionId):
            #print(sectionId)
            return []
        return self.sectionToTrackMap.get(sectionId)

    def updateSectionToTrackMap(self, trackId, sectionId):
        if not self.sectionToTrackMap.get(sectionId): self.sectionToTrackMap[sectionId] = []
        self.sectionToTrackMap[sectionId].append(trackId)

    def getTrackData(self, trackId):
        #sectionIds = self.getSectionsForTrack(trackId)
        #trackData = {trackId:[], 'durations':[], 'markers':[]}
        return self.tracks.get(trackId)

    def getTracks(self):
        return list(self.tracks.keys())

    def updateChunk(self, chunkId, data):
        if not self.tracks.get(chunkId): self.tracks[chunkId] = {}
        for key in data:
            if self.tracks[chunkId].get(key):
                self.tracks[chunkId][key] += data[key]
            else:
                self.tracks[chunkId][key] = data[key]

    def getChunk(self, chunkId):
        return self.tracks.get(chunkId)

    def getKeys(self):
        return list(self.tracks.keys())

    def __str__(self):
        return "Bank: " + str(self.size) + " bytes, " + str(self.numtracks) + " items"
