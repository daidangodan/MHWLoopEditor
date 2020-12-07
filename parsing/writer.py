import struct

class Writer:

    def __init__(self, data):
        self.data = data

    def writeDouble(self, value, offset):
        self.data.seek(offset)
        bytes = struct.pack("d", value)
        self.data.write(bytes)