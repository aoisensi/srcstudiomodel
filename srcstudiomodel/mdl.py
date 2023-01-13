from io import BufferedReader
from typing import List, Tuple

from .util import _struct_unpack


def _read_name64(buf: BufferedReader) -> str:
    return buf.read(64).decode().rstrip('\0')


def _read_strings(buf: BufferedReader, off: int, num: int = 1) -> List[str]:
    start = buf.tell()
    buf.seek(off)
    result = [''] * num
    for i in range(num):
        s = b''
        while True:
            p = buf.read(1)
            if p == b'\0':
                break
            s += p
        result[i] = s.decode()
    buf.seek(start)
    return result


class MDLMesh:
    material: int
    model_index: int
    num_vertices: int
    vertex_offset: int
    num_flexes: int
    flex_index: int
    material_type: int
    material_params: int
    mesh_id: int
    center: Tuple[float, float, float]

    def __init__(self, buf: BufferedReader):
        (self.material, self.model_index, self.num_vertices,
         self.vertex_offset, self.num_flexes, self.flex_index,
         self.material_type, self.material_params, self.mesh_id) \
            = _struct_unpack('=iiiiiiiii', buf)
        self.center = _struct_unpack('=fff', buf)
        buf.seek(68, 1)  # this need fix in future


class MDLModel:
    name: str
    type: int
    bounding_radius: float
    num_meshes: int
    mesh_index: int
    num_vertices: int
    vertex_index: int
    tangents_index: int
    num_attachments: int
    attachment_index: int
    num_eyeballs: int
    eyeball_index: int

    meshes: List[MDLMesh]

    def __init__(self, buf: BufferedReader):
        start = buf.tell()
        self.name = _read_name64(buf)
        (self.type, self.bounding_radius, self.num_meshes, self.mesh_index,
         self.num_vertices, self.vertex_index, self.tangents_index,
         self.num_attachments, self.attachment_index, self.num_eyeballs,
         self.eyeball_index) = _struct_unpack('=ifiiiiiiiii', buf)
        end = buf.seek(40, 1)
        buf.seek(start + self.mesh_index)
        self.meshes = list(map(MDLMesh, [buf]*self.num_meshes))
        buf.seek(end)


class MDLTexture:
    name: str
    flags: int
    used: int

    def __init__(self, buf: BufferedReader):
        start = buf.tell()
        (name_index, self.flags, self.used) = \
            _struct_unpack('=iii', buf)
        self.name = _read_strings(buf, start + name_index)[0]
        buf.seek(52, 1)


class MDLBodyPart:
    num_models: int
    model_index: int

    name: str
    models: List[MDLModel]

    def __init__(self, buf: BufferedReader):
        start = buf.tell()
        (name_index, self.num_models, _, self.model_index) = \
            _struct_unpack('=iiii', buf)
        end = buf.tell()
        self.name = _read_strings(buf, start + name_index)[0]
        buf.seek(start + self.model_index)
        self.models = list(map(MDLModel, [buf]*self.num_models))
        buf.seek(end)


class MDL:
    version: int
    checksum: int
    name: str
    # skipped many entries
    flags: int
    # skipped many entries

    textures: List[MDLTexture]
    skins: List[List[MDLTexture]]
    bodyparts: List[MDLBodyPart]

    def __init__(self, buf: BufferedReader):
        (id, self.version, self.checksum) = _struct_unpack('=III', buf)
        if id != 0x54534449:
            raise Exception('this is not mdl file')
        self.name = _read_name64(buf)
        buf.seek(76, 1)
        self.flags = _struct_unpack('=I', buf)[0]
        buf.seek(48, 1)
        # texture
        (num, off) = _struct_unpack('=ii', buf)
        home = buf.tell()
        buf.seek(off)
        self.textures = list(map(MDLTexture, [buf]*num))
        buf.seek(home + 8)
        # skins
        (num, fnum, off) = _struct_unpack('=iii', buf)
        home = buf.tell()
        buf.seek(off)
        self.skins = [
            [self.textures[_struct_unpack('=h', buf)[0]]
             for _ in range(num)] for _ in range(fnum)
        ]
        buf.seek(home)

        # bodypart
        (num, off) = _struct_unpack('=ii', buf)
        buf.seek(off)
        self.bodyparts = list(map(MDLBodyPart, [buf]*num))
        # home = buf.tell()
