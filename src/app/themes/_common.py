from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from displayio import Group

font_bitocra = bitmap_font.load_font("/bitocra7.bdf")

splash_boot = Group()
splash_boot.append(
    Label(x=5, y=5, text="jinglemansweep", font=font_bitocra, color=0x666666)
)

splash_boot.append(
    Label(x=5, y=25, text="loading...", font=font_bitocra, color=0x666600)
)
