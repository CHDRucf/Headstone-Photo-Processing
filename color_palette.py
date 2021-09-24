# Headstone Photograph Processing System
# Color Palette for the User Interface
# Provides a mechanism to store all of the colors used throughout the program
# To change the program's colors, just change them here

class Color_Palette:
    def __init__(self, fg="#7EC8E3", bg="#050A30", accent="#000C66", accent2="#0000FF", debug="#FF0000"):
        self.fg = fg
        self.bg = bg
        self.accent = accent
        self.accent2 = accent2
        self.debug = debug

color_pallette = Color_Palette()