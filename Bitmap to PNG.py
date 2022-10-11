from math import ceil
from zlib import compress
from time import time

startTime = time()

# Following two paragraphs provided by http://www.libpng.org/pub/png/spec/1.2/PNG-CRCAppendix.html

hexA = int('EDB88320', 16)
hexB = int('FF', 16)
hexC = int('FFFFFFFF', 16)

# Makes CRC Table
crcTable = []
for i in range(256):
    c = i
    for j in range(8):
        if c & 1:
            c = hexA ^ (c >> 1)
        else:
            c = c >> 1
    crcTable.append(c)


def findCRC(words):
    crc = hexC
    for i in range(len(words)):
        crc = crcTable[(crc ^ words[i]) & hexB] ^ (crc >> 8)
    return (crc ^ hexC) % (1 << 32)

data = []
words = []

fileName = 'Academy Island/AcadamyIslandMap1'

with open(fileName + '.bmp', 'rb') as f:
    byte = f.read(1)
    while byte:
        data.append(int.from_bytes(byte, 'big'))
        byte = f.read(1)

with open(fileName + '.png', 'wb') as f:
    def writes(x, size):
        """
        writes converts an integer to a series of bytes, the number of which is specified by the user
        big-endian

        :x: the integer
        :size: the number of bytes to write
        """

        x = int(x)

        for i in range(size):
            word = 8 * (size - i - 1)
            byte = x >> word
            x = x - (byte << word)
            f.write(bytes([byte]))
            words.append(byte)

    # File Header - 8 Bytes
    writes(137, 1) # TXT file discriminator - 1 Byte
    f.write(bytes('PNG', 'ascii')) # Header - 3 Bytes
    writes(3338, 2) # DOS-Unix line ending conversion detection - 2 Bytes
    writes(26, 1) # End of file character - 1 Byte
    writes(10, 1) # Unix-Dos line ending conversion detection - 1 Byte

    # IHDR Chunk - 19 Bytes
    writes(13, 4) # Chunk length - 4 Bytes
    f.write(bytes('IHDR', 'ascii')) # Chunk name - 4 Bytes
    words = [ord('I'), ord('H'), ord('D'), ord('R')] # Resets words for CRC
    # Image MetaData - 13 Bytes
    if data[14] != 12:
        # Width - 4 Bytes
        writes(data[21], 1)
        writes(data[20], 1)
        writes(data[19], 1)
        writes(data[18], 1)
        imgWidth = data[18] + (data[19] << 8) + (data[20] << 16) + (data[21] << 24)
        # Length - 4 Bytes
        writes(data[25], 1)
        writes(data[24], 1)
        writes(data[23], 1)
        writes(data[22], 1)
        imgLength = data[22] + (data[23] << 8) + (data[24] << 16) + (data[25] << 24)
        writes(data[28], 1) # Bit depth - 1 Byte
        bitDepth = data[28]
        if bitDepth == 1 or bitDepth == 2 or bitDepth == 4 or bitDepth == 8:
            writes(3, 1) # Color type - 3 is Indexed - 1 Byte
        elif bitDepth == 16:
            writes(6, 1) # Color type - 6 is RGBA - 1 Byte
        else:
            raise Exception(f'File formats of {data[28]} bits of color depth are not supported at this time.')
        writes(0, 1) # Compression method always 0 - 1 Byte
        writes(0, 1) # Filter method always 0 - 1 Byte
        writes(0, 1) # Interlace method - 0 is no interlace - 1 Byte
    else:
        # Width - 4 Bytes
        writes(0, 2)
        writes(data[19], 1)
        writes(data[18], 1)
        imgWidth = data[18] + data[19] << 8
        # Length - 4 Bytes
        writes(0, 2)
        writes(data[21], 1)
        writes(data[20], 1)
        imgLength = data[20] + data[21] << 8
        writes(data[24], 1) # Bit depth - 1 Byte
        bitDepth = data[24]
        if bitDepth == 1 or bitDepth == 2 or bitDepth == 4 or bitDepth == 8:
            writes(3, 1) # Color type - 3 is Indexed - 1 Byte
        else:
            raise Exception(f'File formats of {data[28]} bits of color depth are not supported at this time.')
    # CRC
    writes(findCRC(words), 4)

    # PLTE Chunk - 3 * n colors  + 12 Bytes
    if bitDepth == 1 or bitDepth == 2 or bitDepth == 4 or bitDepth == 8:
        colorStartIndex = 14 + data[14]
        colorEndIndex = data[10]

        if data[14] != 12:
            writes(int((colorEndIndex - colorStartIndex) / 4) * 3, 4) # Length - 4 Bytes
            f.write(bytes('PLTE', 'ascii')) # Chunk name - 4 Bytes
            words = [ord('P'), ord('L'), ord('T'), ord('E')] # Resets words for CRC

            # Color Palette
            for i in range(colorStartIndex, colorEndIndex, 4):
                writes(data[i + 2], 1) # R - 1 Byte
                writes(data[i + 1], 1) # G - 1 Byte
                writes(data[i], 1) # B - 1 Byte
        else:
            writes(colorEndIndex - colorStartIndex, 4) # Length - 4 Bytes
            f.write(bytes('PLTE', 'ascii')) # Chunk name - 4 Bytes
            words = [ord('P'), ord('L'), ord('T'), ord('E')] # Resets words for CRC

            # Color Palette
            for i in range(colorStartIndex, colorEndIndex, 3):
                writes(i + 2, 1) # R - 1 Byte
                writes(i + 1, 1) # G - 1 Byte
                writes(i, 1) # B - 1 Byte

        # CRC
        writes(findCRC(words), 4)
    
    # IDAT Chunk - Image size + 12 Bytes
    rowSize = ceil(bitDepth * imgWidth / 32) * 4
    scanlineSize = ceil(bitDepth * imgWidth / 8)
    
    imgData = bytearray()
    for i in range(imgLength):
        imgData.append(0)
        for j in range(scanlineSize):
            entry = (i + 1) * -1 * rowSize + j
            point = data[entry]
            imgData.append(data[(i + 1) * -1 * rowSize + j])

    imgDataCompressed = compress(imgData)

    writes(len(imgDataCompressed), 4) # Chunk Length
    f.write(bytes('IDAT', 'ascii'))
    words = [ord('I'), ord('D'), ord('A'), ord('T')]
    for b in imgDataCompressed:
        writes(b, 1)

    # CRC
    writes(findCRC(words), 4)

    # IEND Chunk - 12 Bytes
    writes(0, 4) # Chunk length - 4 Bytes
    f.write(bytes('IEND', 'ascii')) # Chunk name - 4 Bytes
    words = [ord('I'), ord('E'), ord('N'), ord('D')]
    writes(findCRC(words), 4) # CRC

print("%s seconds" % (time() - startTime))