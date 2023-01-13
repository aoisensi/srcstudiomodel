from io import BufferedReader
from typing import List, Tuple

from srcstudiomodel.mdl_enum import MDLFlag

from .util import _struct_unpack
from .type import Matrix3x4, Vector3, Vector4


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


class MDLBone:
    name: str
    parent_id: int
    parent: 'MDLBone'
    children: List['MDLBone']
    bone_controller: List[int]
    pos: Vector3
    quat: Vector4
    rot: Vector3
    posscale: Vector3
    rotscale: Vector3
    pose_to_bone: Matrix3x4
    q_alignment: Vector4
    flags: int
    proctype: int
    procindex: int
    physics_bone: int
    surface_prop_index: int
    contents: int
    # unused 32 bytes

    def __init__(self, buf: BufferedReader):
        start = buf.tell()
        (name_index, self.parent_id) = _struct_unpack('=ii', buf)
        self.name = _read_strings(buf, start+name_index)[0]
        self.bone_controller = list(_struct_unpack('=iiiiii', buf))
        self.pos = _struct_unpack('=fff', buf)
        self.quat = _struct_unpack('=ffff', buf)
        self.rot = _struct_unpack('=fff', buf)
        self.posscale = _struct_unpack('=fff', buf)
        self.rotscale = _struct_unpack('=fff', buf)
        self.pose_to_bone = (
            _struct_unpack('=ffff', buf),
            _struct_unpack('=ffff', buf),
            _struct_unpack('=ffff', buf),
        )
        self.q_alignment = _struct_unpack('=ffff', buf)
        (self.flags, self.proctype, self.procindex, self.physics_bone,
         self.surface_prop_index, self.contents) \
            = _struct_unpack('=iiiiii', buf)
        self.children = []
        buf.seek(32, 1)


class MDL:
    version: int
    checksum: int
    name: str
    # skipped many entries
    flags: MDLFlag
    # skipped many entries

    bones: List[MDLBone]
    root_bone: MDLBone
    textures: List[MDLTexture]
    skins: List[List[MDLTexture]]
    bodyparts: List[MDLBodyPart]

    def __init__(self, buf: BufferedReader):
        (id, self.version, self.checksum) = _struct_unpack('=III', buf)
        if id != 0x54534449:
            raise Exception('this is not mdl file')
        self.name = _read_name64(buf)
        buf.seek(76, 1)
        self.flags = MDLFlag(_struct_unpack('=I', buf)[0])
        # bone
        (num, off) = _struct_unpack('=ii', buf)
        home = buf.tell()
        buf.seek(off)
        self.bones = list(map(MDLBone, [buf]*num))
        buf.seek(home + 40)
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
        self._bone_assemble()

    def _bone_assemble(self):
        for bone in self.bones:
            if bone.parent_id < 0:
                self.root_bone = bone
                continue
            parent = self.bones[bone.parent_id]
            bone.parent = parent
            parent.children.append(bone)
