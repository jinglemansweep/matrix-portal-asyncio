import gc
import math
import time
from displayio import Palette, OnDiskBitmap
from cedargrove_palettefader.palettefader import PaletteFader

PALETTE_GAMMA = 1.0
PALETTE_BRIGHTNESS = 0.1
PALETTE_NORMALIZE = True


def matrix_rotation(accelerometer):
    return (
        int(
            (
                (
                    math.atan2(
                        -accelerometer.acceleration.y, -accelerometer.acceleration.x
                    )
                    + math.pi
                )
                / (math.pi * 2)
                + 0.875
            )
            * 4
        )
        % 4
    ) * 90


def copy_update_palette(palette, updates=None):
    return palette
    if updates is None:
        updates = dict()
    palette_clone = Palette(len(palette))
    for i, color in enumerate(palette):
        if palette.is_transparent(i):
            palette_clone.make_transparent(i)
        if i in updates:
            palette_clone[i] = updates[i]
        else:
            palette_clone[i] = color
    return palette_clone


def load_sprites_brightness_adjusted(
    filename,
    brightness=PALETTE_BRIGHTNESS,
    gamma=PALETTE_GAMMA,
    normalize=PALETTE_NORMALIZE,
    transparent_index=None,
):
    gc.collect()
    bitmap = OnDiskBitmap(filename)
    palette = bitmap.pixel_shader
    if transparent_index is not None:
        palette.make_transparent(transparent_index)
    palette_adj = PaletteFader(
        palette, PALETTE_BRIGHTNESS, PALETTE_GAMMA, PALETTE_NORMALIZE
    )
    return bitmap, palette_adj.palette


def parse_timestamp(timestamp, is_dst=-1):
    # 2022-11-04 21:46:57.174 308 5 +0000 UTC
    bits = timestamp.split(" ")
    year_month_day = bits[0].split("-")
    hour_minute_second = bits[1].split(":")
    return time.struct_time(
        (
            int(year_month_day[0]),
            int(year_month_day[1]),
            int(year_month_day[2]),
            int(hour_minute_second[0]),
            int(hour_minute_second[1]),
            int(hour_minute_second[2].split(".")[0]),
            -1,
            -1,
            is_dst,
        )
    )
