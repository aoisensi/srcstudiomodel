from io import BufferedReader
import struct

def _struct_unpack(format: str, buf: BufferedReader) -> tuple:
    return struct.unpack(format, buf.read(struct.calcsize(format)))