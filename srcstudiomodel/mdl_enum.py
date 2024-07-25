from enum import IntFlag, auto


class MDLFlag(IntFlag):
    AUTOGENERATED_HITBOX = 1 << 0
    USES_ENV_CUBEMAP = 1 << 1
    FORCE_OPAQUE = 1 << 2
    TRANSLUCENT_TWOPASS = 1 << 3
    STATIC_PROP = 1 << 4
    USES_FB_TEXTURE = 1 << 5
    HASSHADOWLOD = 1 << 6
    USES_BUMPMAPPING = 1 << 7
    USE_SHADOWLOD_MATERIALS = 1 << 8
    OBSOLETE = 1 << 9
    UNUSED = 1 << 10
    NO_FORCED_FADE = 1 << 11
    FORCE_PHONEME_CROSSFADE = 1 << 12
    CONSTANT_DIRECTIONAL_LIGHT_DOT = 1 << 13
    FLEXES_CONVERTED = 1 << 14
    BUILT_IN_PREVIEW_MODE = 1 << 15
    AMBIENT_BOOST = 1 << 16
    DO_NOT_CAST_SHADOWS = 1 << 17
    CAST_TEXTURE_SHADOWS = 1 << 18


class MDLAnimFlag(IntFlag):
    STUDIO_ANIM_RAWPOS = 1 << 0
    STUDIO_ANIM_RAWROT = 1 << 1
    STUDIO_ANIM_ANIMPOS = 1 << 2
    STUDIO_ANIM_ANIMROT = 1 << 3
    STUDIO_ANIM_DELTA = 1 << 4
    STUDIO_ANIM_RAWROT2 = 1 << 5


class MDLAnimDescFlag(IntFlag):
    STUDIO_LOOPING = auto()
    STUDIO_SNAP = auto()
    STUDIO_DELTA = auto()
    STUDIO_AUTOPLAY = auto()
    STUDIO_POST = auto()
    STUDIO_ALLZEROS = auto()
    _ = auto()
    STUDIO_CYCLEPOSE = auto()
    STUDIO_REALTIME = auto()
    STUDIO_LOCAL = auto()
    STUDIO_HIDDEN = auto()
    STUDIO_OVERRIDE = auto()
    STUDIO_ACTIVITY = auto()
    STUDIO_EVENT = auto()
    STUDIO_WORLD = auto()
