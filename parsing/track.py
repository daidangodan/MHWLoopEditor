class Track(object):

	def __init__(self, trackId):
		self.sections = []
		self.lengthOffsets = []
		self.trackId = trackId

		self.original = {'length':None}

	def setLength(self, length):
		if self.original['length'] is None:
			self.original['length'] = length
		self.length = length

	def getCurLength(self):
		return self.lengthVar.get()

	def setVars(self, lengthVar):
		self.lengthVar = lengthVar

	def applyChanges(self):
		self.length = self.getCurLength()
		for section in self.sections:
			section.applyChanges()

	def writeToFile(self, writer):
		for lOff in self.lengthOffsets:
			writer.writeDouble(self.length, lOff)
		## have each section write itself to the file ##
		for section in self.sections:
			section.writeToFile(writer)

	def addSection(self, section):
		self.sections.append(section)

	def addLengthOffset(self, offset):
		self.lengthOffsets.append(offset)

class Section(object):

	def __init__(self, sectionId):
		self.playlist = []
		self.durationOffsets = []
		self.sectionId = sectionId

		self.original = {'duration':None}

	def setDuration(self, duration):
		if self.original['duration'] is None:
			self.original['duration'] = duration
		self.duration = duration

	def getCurDuration(self):
		return self.durVar.get()

	def setVars(self, durVar):
		self.durVar = durVar

	def applyChanges(self):
		self.duration = self.getCurDuration()
		for clip in self.playlist:
			clip.applyChanges()

	def writeToFile(self, writer):
		for dOff in self.durationOffsets:
			writer.writeDouble(self.duration, dOff)
		## have each clip write itself to the file ##
		for clip in self.playlist:
			clip.writeToFile(writer)

	def addClip(self, clip):
		self.playlist.append(clip)

	def addDurationOffsets(self, offsets):
		self.durationOffsets += offsets

class Clip(object):

	def __init__(self, play, begin, remain, track):
		self.play = play
		self.begin = begin
		self.remain = remain
		self.track = track

		self.original = {'play': play, 'begin': begin, 'remain': remain}

		self.playOffsets = []
		self.beginOffsets = []
		self.remainOffsets = []

	def getStart(self):
		return abs(self.play)

	def getEnd(self):
		return self.track.length + self.remain

	def getSectionLength(self):
		return self.getEnd() - self.getStart()

	def getCurStart(self):
		return self.start.get()

	def getCurEnd(self):
		return self.end.get()

	def setVars(self, startVar, endVar):
		self.start = startVar
		self.end = endVar

	def applyChanges(self):
		self.begin = self.getCurStart()
		self.play = self.begin * -1
		self.remain = self.getCurEnd() - self.track.length

	def update(self, start, end):
		self.play = start * -1
		self.begin = start
		self.remain = end - self.track.length
		return

	def writeToFile(self, writer):
		for pOff in self.playOffsets:
			writer.writeDouble(self.play, pOff)
		for bOff in self.beginOffsets:
			writer.writeDouble(self.begin, bOff)
		for rOff in self.remainOffsets:
			writer.writeDouble(self.remain, rOff)

	def addPlayOffset(self, offset):
		self.playOffsets.append(offset)

	def addBeginOffset(self, offset):
		self.beginOffsets.append(offset)

	def addRemainOffset(self, offset):
		self.remainOffsets.append(offset)