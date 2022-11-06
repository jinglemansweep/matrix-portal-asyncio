print("BOOT: code.py")

from app import Manager
from app.themes.mario import MarioTheme

manager = Manager(theme=MarioTheme)
manager.run()
