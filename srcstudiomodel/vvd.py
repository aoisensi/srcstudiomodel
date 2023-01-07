from io import BufferedReader
from typing import List, Tuple

from .const import _MAX_NUM_LODS, _MAX_NUM_BONES_PER_VERT
from .util import _struct_unpack

class VVDFixup:
    lod: int
    source_vertex_id: int
    num_vertexes: int

    def __init__(self, buf: BufferedReader):
        (self.lod, self.source_vertex_id, self.num_vertexes) = \
            _struct_unpack('=iii', buf)

class VVDBoneWeight:
    weight: List[float]
    bone: List[int]
    numbones: int

    _format = '=' + 'f'*_MAX_NUM_BONES_PER_VERT + 'c'*_MAX_NUM_BONES_PER_VERT + 'B'

    def __init__(self, buf: BufferedReader):
        values = _struct_unpack(VVDBoneWeight._format, buf)
        self.weight = list(values[:_MAX_NUM_BONES_PER_VERT])
        self.bone = list(values[_MAX_NUM_BONES_PER_VERT:_MAX_NUM_BONES_PER_VERT*2])
        self.numbones = values[-1]

class VVDVertex:
    bone_weights: VVDBoneWeight
    position: Tuple[float, float, float]
    normal: Tuple[float, float, float]
    tex_coord: Tuple[float, float]

    def __init__(self, buf: BufferedReader):
        self.bone_weights = VVDBoneWeight(buf)
        self.position = _struct_unpack('=fff', buf)
        self.normal = _struct_unpack('=fff', buf)
        self.tex_coord = _struct_unpack('=ff', buf)

class VVD:
    version: int
    checksum: int
    num_lods: int
    num_lod_vertexes: List[int]
    fixups: List[VVDFixup]
    vertexes: List[VVDVertex]
    tangents: List[Tuple[float, float, float, float]]

    def __init__(self, buf: BufferedReader):
        start = buf.seek(0, 1)

        (id, self.version, self.checksum, self.num_lods) = \
            _struct_unpack('=IIIi', buf)
        if id != 0x56534449:
            raise Exception('this is not vvd file.')
        self.num_lod_vertexes = list(map(lambda _: _struct_unpack('=i', buf)[0], range(_MAX_NUM_LODS)))
        (num_fixups, fixup_stable_start, vertex_data_start, tangent_data_start) = \
            _struct_unpack('=iiii', buf)

        buf.seek(start + fixup_stable_start)
        self.fixups = list(map(VVDFixup, [buf] * num_fixups))

        buf.seek(start + vertex_data_start)
        self.vertexes = list(map(VVDVertex, [buf] * self.num_lod_vertexes[0]))

        buf.seek(start + tangent_data_start)
        self.tangents = list(map(lambda _: _struct_unpack('=ffff', buf), range(self.num_lod_vertexes[0])))


