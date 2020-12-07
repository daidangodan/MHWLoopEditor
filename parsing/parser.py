from .reader import *
from .bank import *

types = ['01','02','03','04','05','06','07','08','09','0a','0b','0c','0d','0e','0f','10','11','12','13','14','15','16']

# def parse(path: str): -> None
def parse(path, validate=False, print=False):
    if validate:
        offsets = parseText()
    with open(path, "rb") as nbnk:
        reader = Reader(nbnk)
        reader.advance(4)
        headerSize = reader.readUInt32()
        reader.advance(headerSize)
        rootHeader = reader.readString(4)
        if (rootHeader != 'HIRC'):
            print('Header was not HIRC: ' + rootHeader)
            return
        hircSize = reader.readUInt32()
        numItems = reader.readUInt32()
        bank = Bank(hircSize, numItems)
        for i in range(numItems):
            curOffset = hex(reader.data.tell())
            type = reader.readHexString(1)
            if validate:
                if type != offsets[i][1] or curOffset != offsets[i][0]:
                    print('i: ' + str(i))
                print(f'expected type: {validation[1]} actual: {type}')
                print(f'expected offset: {validation[0]} actual: {curOffset}')
                return
            if type == '0b': # MUSIC TRACK
                reader.readTrack(bank)
            elif type == '0a': # MUSIC SEGMENT
                reader.readSegment(bank)
            else:
                chunkSize = reader.readUInt32()
                reader.advance(chunkSize)
        if print:
            outputToFile('output/parsed.txt', bank)
        return bank

def parseText():
    offsets = []
    with open("resources/test.txt", "r") as nbnk:
        for line in nbnk.readlines():
            if ("eHircType" in line):
                offset = '0x' + line.split(" ", 1)[0].lstrip('0')
                type = line.split("=")[1].split(" ")[1][2:].lower()
                offsets.append((offset, type))
    return offsets

def outputToFile(filename, bank):
    parsedData = open(filename, 'w')
    trackIds = bank.getTracks()
    for tid in trackIds:
        parsedData.write(f'{tid}:\n')
        trackData = bank.getTrackData(tid)
        sectionIds = list(trackData.keys())
        for i in range(len(sectionIds)):
            parsedData.write(f'  {sectionIds[i]}:\n')
            parsedData.write(f'    {trackData[i]}\n')
    parsedData.close