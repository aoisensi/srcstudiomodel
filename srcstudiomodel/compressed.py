from io import BufferedReader
import math
from srcstudiomodel.type import Vector3, Vector4
from srcstudiomodel.util import _struct_unpack

# *******************
# compressed_vector.h
# *******************

_bits10 = 0b1111111111
_bits15 = 0b111111111111111
_bits16 = 0b1111111111111111
_bits21 = 0b111111111111111111111


def vec32(buf: BufferedReader) -> Vector3:
    v = int.from_bytes(buf.read(4), 'little')
    x = v >> 00 & _bits10
    y = v >> 10 & _bits10
    z = v >> 20 & _bits10
    e = v >> 30 & 0b11
    f = [4.0, 16.0, 32.0, 64.0][e] / 512.0
    return ((x - 512) * f, (y - 512) * f, (z - 512) * f)


def vec48(buf: BufferedReader) -> Vector3:
    return _struct_unpack('=eee', buf)


def quat48(buf: BufferedReader) -> Vector4:
    v = int.from_bytes(buf.read(6), 'little')
    div = (1.0 / 32768.0)
    x = ((v >> 00 & _bits16) - 32768) * div
    y = ((v >> 16 & _bits16) - 32768) * div
    z = ((v >> 32 & _bits15) - 16384) * (1.0 / 16384.0)
    w = math.sqrt(1.0 - x*x - y*y - z*z)
    if v & (1 << 47):
        w = -w
    return (x, y, z, w)


def quat64(buf: BufferedReader) -> Vector4:
    v = int.from_bytes(buf.read(8), 'little')
    div = (1.0 / 1048576.5)
    x = ((v >> 00 & _bits21) - 1048576) * div
    y = ((v >> 21 & _bits21) - 1048576) * div
    z = ((v >> 42 & _bits21) - 1048576) * div
    w = math.sqrt(1.0 - x*x - y*y - z*z)
    if v & (1 << 63):
        w = -w
    return (x, y, z, w)
