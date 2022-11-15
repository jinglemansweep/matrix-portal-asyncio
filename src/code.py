print("BOOT: code.py")

import displayio

displayio.release_displays()


from app import Manager
from app.themes.mario import MarioTheme

manager = Manager(theme=MarioTheme)
manager.run()
