from adafruit_display_text.label import Label
from displayio import Group


def build_splash_group(font):
    group = Group()
    group.append(Label(x=5, y=5, text="jinglemansweep", font=font, color=0x666666))
    group.append(Label(x=5, y=25, text="loading...", font=font, color=0x666600))
    return group
