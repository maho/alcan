from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

from anim import AnimObject
import defs


class Hint(BoxLayout):
    pass
    # def __init__(self):
    #     super(Hint, self).__init__()


class GameOver(AnimObject):
    def __init__(self, *a, **kw):
        super(GameOver, self).__init__(*a, **kw)
        self.layers = -1 - defs.CARRIED_THINGS_LAYER
    
    def on_touch_up(self, touch):
        App.get_running_app().root.gameover()


class Success(BoxLayout):

    def on_touch_up(self, touch):
        App.get_running_app().root.gameover()
