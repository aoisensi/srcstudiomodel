from io import BufferedReader
from typing import List

from .const import _MAX_NUM_BONES_PER_VERT
from .util import _struct_unpack

class MDL:
    version: int
    checksum: int
    name: str
    # skipped many entries
    flags: int
    # skipped many entries

    texture_names: List[str]

    def __init__(self, buf: BufferedReader):
        (id, self.version, self.checksum) = _struct_unpack('=III', buf)
        if id != 0x54534449:
            raise Exception('this is not mdl file')
        self.name = buf.read(64).decode().rstrip('\0')
        buf.seek(76, 1)
        self.flags = _struct_unpack('=I', buf)[0]
