class Track(object):

	def __init__(self):
		self.playlist = []

	def addClip(self, clip):
		self.playlist.append(clip)


class Clip(object):

	def __init__(self, play, begin, remain, length, sectionId):
		self.play = play
		self.begin = begin
		self.remain = remain
		self.length = length
		self.sectionId = sectionId