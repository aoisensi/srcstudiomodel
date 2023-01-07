from io import BufferedReader
from typing import List

from .const import _MAX_NUM_BONES_PER_VERT
from .util import _struct_unpack

class VTXVertex:
    bone_weight_index: List[int]
    num_bones: int
    orig_mesh_vert_id: int
    bone_id: List[int]

    def __init__(self, buf: BufferedReader):
        self.bone_weight_index = list(map(lambda _: _struct_unpack('=B', buf)[0], range(_MAX_NUM_BONES_PER_VERT)))
        (self.num_bones, self.orig_mesh_vert_id) = _struct_unpack('=BH', buf)
        self.bone_id = list(map(lambda _: _struct_unpack('=h', buf)[0], range(_MAX_NUM_BONES_PER_VERT)))

class VTXStrip:
    num_indices: int
    index_offset: int
    num_verts: int
    vert_offset: int
    num_bones: int
    flags: int
    num_bone_state_changes: int # maybe useless
    bone_state_change_offset: int # maybe useless

    def __init__(self, buf: BufferedReader):
        (self.num_indices, self.index_offset, self.num_verts, self.vert_offset, self.num_bones, \
            self.flags, self.num_bone_state_changes, self.bone_state_change_offset) \
            = _struct_unpack('=iiiihBii', buf)

class VTXStripGroup:
    flags: int

    vertexes: List[VTXVertex]
    indices: List[int]
    strips: List[VTXStrip]

    def __init__(self, buf: BufferedReader):
        (vnum, voff, inum, ioff, snum, soff, self.flags) = _struct_unpack('=iiiiiiB', buf)
        end = buf.tell()
        buf.seek(voff - 25, 1)
        self.vertexes = list(map(VTXVertex, [buf] * vnum))
        buf.seek(end + ioff - 25)
        self.indices = list(map(lambda _: _struct_unpack('=H', buf)[0], range(inum)))
        buf.seek(end + soff - 25)
        self.strips = list(map(VTXStrip, [buf] * snum))
        buf.seek(end)


class VTXMesh:
    flags: int
    
    strip_groups: List[VTXStripGroup]

    def __init__(self, buf: BufferedReader):
        (num, offset, self.flags) = _struct_unpack('=iiB', buf)
        end = buf.tell()
        buf.seek(offset - 9, 1)
        self.meshes = list(map(VTXStripGroup, [buf] * num))
        buf.seek(end)

class VTXModelLOD:
    switch_point: float

    meshes: List[VTXMesh]

    def __init__(self, buf: BufferedReader):
        (num, offset, self.switch_point) = _struct_unpack('=iif', buf)
        end = buf.tell()
        buf.seek(offset - 12, 1)
        self.meshes = list(map(VTXMesh, [buf] * num))
        buf.seek(end)

class VTXModel:
    model_lods: List[VTXModelLOD]

    def __init__(self, buf: BufferedReader):
        (num, offset) = _struct_unpack('=ii', buf)
        end = buf.tell()
        buf.seek(offset - 8, 1)
        self.model_lods = list(map(VTXModelLOD, [buf] * num))
        buf.seek(end)

class VTXBodyPart:
    models: List[VTXModel]

    def __init__(self, buf: BufferedReader):
        (num, offset) = _struct_unpack('=ii', buf)
        end = buf.tell()
        buf.seek(offset - 8, 1)
        self.models = list(map(VTXModel, [buf] * num))
        buf.seek(end)


class VTX:
    version: int
    vert_cache_size: int
    max_bones_per_strip: int
    max_bones_per_tri: int
    max_bones_per_vert: int
    checksum: int
    num_lods: int
    material_replacement_list_offset: int

    body_parts: List[VTXBodyPart]

    def __init__(self, buf: BufferedReader):
        (self.version, self.vert_cache_size,
            self.max_bones_per_strip, self.max_bones_per_tri, self.max_bones_per_vert,
            self.checksum, self.num_lods, self.material_replacement_list_offset,
            num_body_parts, body_part_offset) = _struct_unpack('=IiHHiiiiii', buf)
        buf.seek(body_part_offset)
        self.body_parts = list(map(VTXBodyPart, [buf] * num_body_parts))
