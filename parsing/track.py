class Track(object):

	def __init__(self, trackId, sectionId):
		self.playlist = []
		self.durationOffsets = []
		self.lengthOffsets = []
		self.trackId = trackId
		self.sectionId = sectionId

		self.original = {'duration':None, 'length':None}
		self.changed = False

	def setDuration(self, duration):
		if self.original['duration'] is None:
			self.original['duration'] = duration
		else:
			self.changed = True
		self.duration = duration

	def setLength(self, length):
		if self.original['length'] is None:
			self.original['length'] = length
		else:
			self.changed = True
		self.length = length

	def getCurDuration(self):
		return self.durVar.get()

	def getCurLength(self):
		return self.lengthVar.get()

	def setVars(self, durVar, lengthVar):
		self.durVar = durVar
		self.lengthVar = lengthVar

	def applyChanges(self):
		self.duration = self.getCurDuration()
		self.length = self.getCurLength()
		for clip in self.playlist:
			clip.applyChanges(self.length)

	def writeToFile(self, writer):
		for dOff in self.durationOffsets:
			writer.writeDouble(self.duration, dOff)
		for lOff in self.lengthOffsets:
			writer.writeDouble(self.length, lOff)
		## have each clip write itself to the file ##
		for clip in self.playlist:
			clip.writeToFile(writer)

	def addClip(self, clip):
		self.playlist.append(clip)

	def addDurationOffsets(self, offsets):
		self.durationOffsets += offsets

	def addLengthOffset(self, offset):
		self.lengthOffsets.append(offset)


class Clip(object):

	def __init__(self, play, begin, remain, length):
		self.play = play
		self.begin = begin
		self.remain = remain
		self.length = length

		self.original = {'play': play, 'begin': begin, 'remain': remain, 'length': length}

		self.playOffsets = []
		self.beginOffsets = []
		self.remainOffsets = []

	def getStart(self):
		return abs(self.play)

	def getEnd(self):
		return self.length + self.remain

	def getSectionLength(self):
		return self.getEnd() - self.getStart()

	def getCurStart(self):
		return self.start.get()

	def getCurEnd(self):
		return self.end.get()

	def setVars(self, startVar, endVar):
		self.start = startVar
		self.end = endVar

	def applyChanges(self, trackLength):
		self.begin = self.getCurStart()
		self.play = self.begin * -1
		self.remain = self.getCurEnd() - trackLength
		self.length = trackLength

	def update(self, start, end):
		self.play = start * -1
		self.begin = start
		self.remain = end - self.length
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