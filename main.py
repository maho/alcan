import os
import time

from cymunk import BoxShape, PivotJoint, Vec2d
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import ScreenManager

from alcangame import AlcanGame
from anim import AnimObject
import defs
from element import Element
from utils import configure_logger


class Beam(AnimObject):
    def add_body(self, dt=None):
        super(Beam, self).add_body(dt=dt)
        if self.body:  # if obj is initialized ye
            self.body.velocity_limit = 0


class Platform(AnimObject):
    angle = NumericProperty(0)

    def create_shape(self):
        sx, sy = self.size
        shape = BoxShape(self.body, sx, sy)
        shape.elasticity = 0.6
        shape.friction = defs.friction
        shape.collision_type = self.collision_type
        # shape.layers = defs.NORMAL_LAYER

        return shape


class AlcanSM(ScreenManager):

    #def __init__(self, *a, **kw):
    #    super(ScreenManager, self).__init__(*a, **kw)
    #    self.game_clock = None


    def play(self, level):
        self.game_clock = None
        self.current = 'game'

        if level == 'easy':
            defs.explode_when_nocomb = 0.9
            defs.drop_useless_chance = 0.0
            defs.left_beam_fine_pos = - 130
            defs.beam_speed = 10
        elif level == 'medium':
            defs.explode_when_nocomb = 0.5
            defs.drop_useless_chance = 0.3
            defs.left_beam_fine_pos = -10
            defs.beam_speed = 20
        elif level == 'hard':
            defs.explode_when_nocomb = 0.01
            defs.drop_useless_chance = 0.45
            defs.left_beam_fine_pos = +5
            defs.beam_speed = 60

        App.get_running_app().game = AlcanGame()

        self.gameuberlayout.add_widget(App.get_running_app().game)

    def schedule_gameover(self):
        self.game_clock = Clock.schedule_once(self.gameover, 18)

    def gameover(self, dt=None):
        if self.game_clock:
            self.game_clock.cancel()
            self.game_clock = None

        game = self.gameuberlayout.children[0]
        self.gameuberlayout.remove_widget(game)
        game.clear()
        del(game)
        Element.reset()
        self.current = 'main'


class AlcanApp(App):
    def build(self):
        # Window.size = defs.map_size

        self.sm = AlcanSM()
        return self.sm

    def on_pause(self):
       Logger.info("app: on pause calledd")
       return True

    def on_resume(self):
       Logger.info("app: on resume called")
       return True

#     def on_start(self):
#         Logger.info("app: on_start called")
#         return True
# 
#     def on_stop(self):
#         Logger.info("app: on_stop called")
#         return True


if __name__ == '__main__':

    if "DEBUG" in os.environ:
        def debug_signal_handler(signal, frame):
            import pudb
            pudb.set_trace()

        import signal
        signal.signal(signal.SIGINT, debug_signal_handler)

    configure_logger()
    AlcanApp().run()
