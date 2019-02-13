from kivy.core.audio import SoundLoader


class Sounds:
    merge = None


def load_sounds():
    Sounds.merge = SoundLoader.load("sfx/merge.ogg")
