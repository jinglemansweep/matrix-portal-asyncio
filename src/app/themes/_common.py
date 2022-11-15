from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from displayio import Group

font_bitocra = bitmap_font.load_font("/bitocra7.bdf")

splash_boot = Group()
splash_boot.append(Label(x=30, y=10, text="HELLO", font=font_bitocra))
