import os
import sys

def getResourcePath(relativePath):
	try:
		basePath = sys._MEIPASS
	except Exception:
		basePath = os.path.abspath('.')
	return os.path.join(basePath, relativePath)