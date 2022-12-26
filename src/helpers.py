MAX_PLY = 60
CHECK_RATE = 256

VALUE_INFINITE = 32001
VALUE_NONE = 32002
VALUE_MATE = 32000
VALUE_MATE_IN_PLY = VALUE_MATE - MAX_PLY
VALUE_MATED_IN_PLY = -VALUE_MATE_IN_PLY

# Theres no TB support but it useful for other people who port this to another language to respect the TB value ranges
VALUE_TB_WIN = VALUE_MATE_IN_PLY
VALUE_TB_LOSS = -VALUE_TB_WIN
VALUE_TB_WIN_IN_MAX_PLY = VALUE_TB_WIN - MAX_PLY
VALUE_TB_LOSS_IN_MAX_PLY = -VALUE_TB_WIN_IN_MAX_PLY


# least significant bit
def lsb(x: int) -> int:
    return (x & -x).bit_length() - 1


def poplsb(x: int) -> int:
    x &= x - 1
    return x


def mate_in(ply: int) -> int:
    return VALUE_MATE - ply


def mated_in(ply: int) -> int:
    return ply - VALUE_MATE
