from io import BufferedReader
from typing import List, Optional, Tuple

from srcstudiomodel.mdl_enum import MDLAnimDescFlag, MDLAnimFlag, MDLFlag

from .util import _struct_unpack
from .type import Matrix3x4, Vector3, Vector4
from . import compressed


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

    def __str__(self) -> str:
        return self.name


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

    def __str__(self) -> str:
        return self.name


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

    def __str__(self) -> str:
        return self.name


class MDLBone:
    id: int
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

    def __init__(self, id: int, buf: BufferedReader):
        self.id = id
        start = buf.tell()
        (name_index, self.parent_id) = _struct_unpack('=ii', buf)
        self.name = _read_strings(buf, start + name_index)[0]
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

    def __str__(self) -> str:
        return self.name


class MDLMovement:
    end_frame: int
    motion_frags: int
    v0: float
    v1: float
    angle: float
    vector: Vector3
    position: Vector3

    def __init__(self, buf: BufferedReader):
        (self.end_frame, self.motion_frags, self.v0, self.v1, self.angle) = _struct_unpack('=iifff', buf)
        self.vector = _struct_unpack('=fff', buf)
        self.position = _struct_unpack('=fff', buf)


class MDLAnimBlock:
    data_start: int
    data_end: int

    def __init__(self, buf: BufferedReader):
        (self.data_start, self.data_end) = _struct_unpack('=ii', buf)


class MDLAnimValue:
    valid: int
    total: int
    values: List[int]
    next: Optional['MDLAnimValue']

    def __init__(self, buf: BufferedReader, frames_remaining: int):
        (self.valid, self.total) = _struct_unpack('=BB', buf)
        for _ in range(self.valid):
            self.values.append(_struct_unpack('=h', buf)[0])
        if frames_remaining > 0:
            self.next = MDLAnimValue(buf, frames_remaining - self.total)


AnimValues = Tuple[MDLAnimValue, MDLAnimValue, MDLAnimValue]


class MDLAnimValuePtr:
    offsets: Tuple[int, int, int]

    def __init__(self, buf: BufferedReader):
        self.offsets = _struct_unpack('=hhh', buf)


class MDLAnim:
    bone: int
    flags: MDLAnimFlag
    next: Optional['MDLAnim']

    ptr_rot: Optional[AnimValues] = None
    ptr_pos: Optional[AnimValues] = None
    raw_rot: Optional[Vector4] = None
    raw_pos: Optional[Vector3] = None

    def __init__(self, buf: BufferedReader, frames: int):
        start = buf.tell()
        (self.bone, flags, next_index) = _struct_unpack('=BBh', buf)
        self.flags = MDLAnimFlag(flags)
        if self.bone == 255:
            # TODO: implement
            return
        self._read_data(buf, frames)
        end = buf.tell()
        if next_index != 0:
            buf.seek(start + next_index)
            next = MDLAnim(buf, frames)
            if next.bone != 255:
                self.next = next
            buf.seek(end)
        else:
            self.next = None

    def _read_data(self, buf: BufferedReader, frames: int):
        raw = False
        if self.flags & MDLAnimFlag.STUDIO_ANIM_RAWROT:
            self.raw_rot = compressed.quat48(buf)
            raw = True
        elif self.flags & MDLAnimFlag.STUDIO_ANIM_RAWROT2:
            self.raw_rot = compressed.quat64(buf)
            raw = True

        if self.flags & MDLAnimFlag.STUDIO_ANIM_RAWPOS:
            self.raw_pos = compressed.vec48(buf)
            raw = True
        if raw:
            return

        if self.flags & MDLAnimFlag.STUDIO_ANIM_ANIMROT:
            rotp = MDLAnimValuePtr(buf)
        if self.flags & MDLAnimFlag.STUDIO_ANIM_ANIMPOS:
            posp = MDLAnimValuePtr(buf)
        if rotp:
            self.ptr_rot = self._read_three_values(buf, rotp, frames)
        if posp:
            self.ptr_pos = self._read_three_values(buf, posp, frames)

    def _read_three_values(self, buf: BufferedReader, ptrs: MDLAnimValuePtr, frames: int) -> AnimValues:
        start = buf.tell()
        reuslt: List[MDLAnimValue] = []
        for ptr in ptrs.offsets:
            buf.seek(ptr, 1)
            reuslt.append(MDLAnimValue(buf, frames))
        buf.seek(start)
        return (reuslt[0], reuslt[1], reuslt[2])

    def _read_value_ptr(self, buf: BufferedReader) -> Tuple[int, int, int]:
        start = buf.tell()
        return tuple(p + start for p in _struct_unpack('=iii', buf))


class MDLAnimSections:
    anim_block: int
    anim_index: int

    def __init__(self, buf: BufferedReader):
        (self.anim_block, self.anim_index) = _struct_unpack('=ii', buf)


class MDLAnimDesc:
    baseptr: int
    name: str
    fps: float
    flags: MDLAnimDescFlag
    num_frames: int  # frameCount
    num_movement: int
    movement_index: int
    # unused 24 bytes
    anim_block: int
    anim_index: int  # animOffset
    num_ikrule: int
    ikrule_index: int
    animblock_ikrule_index: int
    num_local_hierarchy: int
    local_hierarchy_index: int
    section_index: int  # sectionOffset
    section_frames: int  # sectionFrameCount
    zero_frame_span: int
    zero_frame_count: int
    zero_frame_index: int
    zero_frames_tall_time: float

    movements: List[MDLMovement]
    sections: List[MDLAnimSections]
    anims: List[Optional[MDLAnim]]

    def __init__(self, buf: BufferedReader):
        start = buf.tell()
        (self.baseptr, name_off, self.fps, flags, self.num_frames, self.num_movement,
         self.movement_index) = _struct_unpack('=iifiiii', buf)
        self.flags = MDLAnimDescFlag(flags)
        self.name = _read_strings(buf, start + name_off)[0]
        print(self.name)
        buf.seek(24, 1)
        (self.anim_block, self.anim_index, self.num_ikrule, self.ikrule_index,
         self.animblock_ikrule_index, self.num_local_hierarchy, self.local_hierarchy_index,
         section_index, self.section_frames, self.zero_frame_span, self.zero_frame_count,
         self.zero_frame_index, self.zero_frames_tall_time) = _struct_unpack('=iiiiiiiiihhif', buf)
        end = buf.tell()
        self.anims = [None]

        # Movement
        buf.seek(start + self.movement_index)
        self.movements = list(map(MDLMovement, [buf] * self.num_movement))

        # Section
        if self.section_frames > 0 and section_index != 0:
            buf.seek(start + section_index)
            section_num = (self.num_frames // self.section_frames + 2)
            self.sections = list(map(MDLAnimSections, [buf] * section_num))
            self.anims = [None] * section_num
        else:
            self.sections = []

        # Animation
        if self.sections:
            for i, section in enumerate(self.sections):
                if section.anim_block == 0:
                    offset = section.anim_index + self.anim_index - self.sections[0].anim_index
                    section_frames = self.section_frames
                    if i >= self.section_frames - 1:  # if not last
                        section_frames = self.num_frames - (len(self.sections) - 2) * section_frames
                    buf.seek(start + offset)
                    self._read_anim(buf, section_frames, i)
        # anim block
        # https://github.com/ZeqMacaw/Crowbar/blob/master/Crowbar/Core/GameModel/SourceModel44/SourceMdlFile44.vb#L1070
        elif self.anim_block == 0:
            buf.seek(start + self.anim_index)
            self._read_anim(buf, self.num_frames, 0)
        buf.seek(end)

    def _read_anim(self, buf: BufferedReader, num_frames: int, section_index: int):
        anim = MDLAnim(buf, num_frames)
        if anim.bone < 255:
            self.anims[section_index] = anim

    def __str__(self) -> str:
        return self.name


class MDLSeqDesc:
    baseptr: int
    label: str
    activity_name: str
    flags: int
    activity: int
    actweight: int
    num_events: int
    event_index: int
    bbmin: Vector3
    bbmax: Vector3
    num_blends: int
    anim_index_index: int
    movement_index: int
    group_size: Tuple[int, int]
    param_index: Tuple[int, int]
    param_start: Tuple[float, float]
    param_end: Tuple[float, float]
    param_parent: int
    fade_in_time: float
    fade_out_time: float
    local_entry_node: int
    local_exit_node: int
    node_flags: int
    entry_phase: float
    exit_phase: float
    last_frame: float
    next_seq: int
    pose: int
    num_ik_rules: int
    num_auto_layers: int
    auto_layer_index: int
    weight_list_index: int
    pose_key_index: int
    num_ik_locks: int
    ik_lock_index: int
    keyvalue_index: int
    keyvalue_size: int
    cycle_pose_index: int
    # unused 28 bytes
    anims: List[List[int]]

    def __init__(self, buf: BufferedReader):
        start = buf.tell()
        (self.baseptr, labeloff, anoff) = _struct_unpack('=iii', buf)
        self.label = _read_strings(buf, start + labeloff)[0]
        self.activity_name = _read_strings(buf, start + anoff)[0]
        (self.flags, self.activity, self.actweight, self.num_events, self.event_index) \
            = _struct_unpack('=iiiii', buf)
        self.bbmin = _struct_unpack('=fff', buf)
        self.bbmax = _struct_unpack('=fff', buf)
        (self.num_blends, self.anim_index_index, self.movement_index) = _struct_unpack('=iii', buf)
        self.group_size = _struct_unpack('=ii', buf)
        self.param_index = _struct_unpack('=ii', buf)
        self.param_start = _struct_unpack('=ff', buf)
        self.param_end = _struct_unpack('=ff', buf)
        (self.param_parent, self.fade_in_time, self.fade_out_time, self.local_entry_node,
         self.local_exit_node, self.node_flags, self.entry_phase, self.exit_phase, self.last_frame,
         self.next_seq, self.pose, self.num_ik_rules, self.num_auto_layers, self.auto_layer_index,
         self.weight_list_index, self.pose_key_index, self.num_ik_locks, self.ik_lock_index,
         self.keyvalue_index, self.keyvalue_size, self.cycle_pose_index) \
            = _struct_unpack('=iffiiifffiiiiiiiiiiii', buf)
        end = buf.seek(28, 1)
        buf.seek(start + self.anim_index_index)
        self.anims = [list(_struct_unpack('=' + 'h' * self.group_size[0], buf)) for _ in range(self.group_size[1])]
        buf.seek(end)

    def __str__(self) -> str:
        return self.label


class MDL:
    version: int
    checksum: int
    name: str
    # skipped many entries
    flags: MDLFlag
    # skipped many entries

    bones: List[MDLBone]
    root_bone: MDLBone
    anim_descs: List[MDLAnimDesc]
    seq_descs: List[MDLSeqDesc]
    textures: List[MDLTexture]
    skins: List[List[MDLTexture]]
    bodyparts: List[MDLBodyPart]
    anim_block_name: str
    anim_blocks: List[MDLAnimBlock]

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
        self.bones = list(map(lambda arg: MDLBone(arg[0], arg[1]), enumerate([buf]*num)))
        buf.seek(home + 16)
        # animdesc
        (num, off) = _struct_unpack('=ii', buf)
        home = buf.tell()
        buf.seek(off)
        self.anim_descs = list(map(MDLAnimDesc, [buf]*num))
        buf.seek(home)
        # seqdesc
        (num, off) = _struct_unpack('=ii', buf)
        home = buf.tell()
        buf.seek(off)
        self.seq_descs = list(map(MDLSeqDesc, [buf]*num))
        buf.seek(home + 8)
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
        home = buf.tell()
        buf.seek(off)
        self.bodyparts = list(map(MDLBodyPart, [buf]*num))
        # anim_blocks
        buf.seek(home + 27*4)
        (name_index, num, off) = _struct_unpack('=iii', buf)
        home = buf.tell()
        self.anim_block_name = _read_strings(buf, name_index)[0]
        buf.seek(off)
        self.anim_blocks = list(map(MDLAnimBlock, [buf]*num))

        # assemples
        self._bone_assemble()

    def _bone_assemble(self):
        for bone in self.bones:
            if bone.parent_id < 0:
                self.root_bone = bone
                continue
            parent = self.bones[bone.parent_id]
            bone.parent = parent
            parent.children.append(bone)

    def __str__(self) -> str:
        return self.name
