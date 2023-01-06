from io import BufferedReader
import struct
from typing import List, Tuple

from .const import _MAX_NUM_LODS, _MAX_NUM_BONES_PER_VERT
from .util import _struct_unpack

class VVDFixup:
    lod: int
    source_vertex_id: int
    num_vertexes: int

    def __init__(self, buf: BufferedReader) -> 'VVDFixup':
        (self.lod, self.source_vertex_id, self.num_vertexes) = \
            _struct_unpack('iii', buf)

class VVDBoneWeight:
    weight: List[float]
    bone: List[int]
    numbones: int

    def __init__(self, buf: BufferedReader) -> 'VVDBoneWeight':
        self.weight = list(_struct_unpack('f'*_MAX_NUM_BONES_PER_VERT, buf))
        self.bone = list(_struct_unpack('c'*_MAX_NUM_BONES_PER_VERT, buf))
        self.numbones = _struct_unpack('B', buf)

class VVDVertex:
    bone_weights: VVDBoneWeight
    position: Tuple[float, float, float]
    normal: Tuple[float, float, float]
    tex_coord: Tuple[float, float]

    def __init__(self, buf: BufferedReader) -> 'VVDVertex':
        self.bone_weights = VVDBoneWeight(buf)
        self.position = _struct_unpack('fff', buf)
        self.normal = _struct_unpack('fff', buf)
        self.tex_coord = _struct_unpack('ff', buf)

class VVD:
    id: int
    version: int
    checksum: int
    num_lods: int
    num_lod_vertexes: List[int]
    fixups: List[VVDFixup]
    vertexes: List[VVDVertex]
    tangents: List[Tuple[float, float, float, float]]

    def __init__(self, buf: BufferedReader) -> 'VVD':
        start = buf.seek(0)

        (self.id, self.version, self.checksum, self.num_lods) = \
            _struct_unpack('iiii', buf)
        self.num_lod_vertexes = list(_struct_unpack('i' * _MAX_NUM_LODS, buf))
        (num_fixups, fixup_stable_start, vertex_data_start, tangent_data_start) = \
            _struct_unpack('iiii', buf)

        buf.seek(start + fixup_stable_start, 0)
        self.fixups = list(map(VVDFixup, [buf] * num_fixups))

        buf.seek(start + vertex_data_start, 0)
        self.vertexes = list(map(VVDVertex, [buf] * self.num_lod_vertexes[0]))

        buf.seek(start + tangent_data_start, 0)
        self.tangents = list(map(lambda _: _struct_unpack('ffff', buf), range(self.num_lod_vertexes[0])))


