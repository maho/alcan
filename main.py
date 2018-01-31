import os
import time

from cymunk import BoxShape, PivotJoint, Vec2d
from kivy.app import App
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget

from alcangame import AlcanGame
from anim import AnimObject, PhysicsObject
from baloon import Baloon
import defs
from element import Element
from utils import report


class Beam(AnimObject):
    pass


class Platform(AnimObject):
    angle = NumericProperty(0)

    def create_shape(self):
        sx, sy = self.size
        shape = BoxShape(self.body, sx, sy)
        shape.elasticity = 0.6
        shape.friction = defs.friction
        shape.collision_type = self.collision_type
        shape.layers = defs.NORMAL_LAYER

        return shape



class Wizard(AnimObject):

    collision_type = 3

    def __init__(self, *a, **kw):
        super(Wizard, self).__init__(*a, mass=defs.wizard_mass, **kw)
        self.layers = defs.NORMAL_LAYER
        self.carried_elements = []
        self.applied_force = Vec2d(0, 0)

    def carry_element(self, element, __dt=None):
        if time.time() - element.released_at < 1.0:
            return True
        # move element to "carried elements layer"
        element.shape.layers = defs.CARRIED_THINGS_LAYER

        # bind it to wizard
        # #move element up
        pivot = self.body.position + Vec2d(defs.wizard_hand)
        element.body.position = pivot
        element.joint = PivotJoint(self.body, element.body, pivot)
        self.space.add(element.joint)

        self.carried_elements.append(element)
        element.wizard = self

    def add_body(self, dt=None):
        super(Wizard, self).add_body(dt=dt)
        if self.body:  # if obj is initialized ye
            self.body.velocity_limit = defs.wizard_max_speed

    def create_shape(self):
        shape = super(Wizard, self).create_shape()
        shape.friction = defs.wizard_friction
        return shape

    def release_element(self):
        if not self.carried_elements:
            return False
        for x in self.carried_elements[:]:
            x.body.apply_impulse(defs.wizard_release_impulse)
            x.unjoint()
            x.shape.layers = defs.NORMAL_LAYER
            x.released_at = time.time()

        return True

class AlcanSM(ScreenManager):

    def play(self, level):
        self.current = 'game'

        if level == 'easy':
            defs.explode_when_nocomb = 0.9
            defs.drop_useless_chance = 0.0
            defs.left_beam_fine_pos = - 30
        elif level == 'medium':
            defs.explode_when_nocomb = 0.5
            defs.drop_useless_chance = 0.3
            defs.left_beam_fine_pos = -10
        elif level == 'hard':
            defs.explode_when_nocomb = 0.1
            defs.drop_useless_chance = 0.5
            defs.left_beam_fine_pos = +5

        self.gameuberlayout.add_widget(AlcanGame())

    def schedule_gameover(self):
        Clock.schedule_once(self.gameover, 4)

    def gameover(self, dt=None):
        game = self.gameuberlayout.children[0]
        self.gameuberlayout.remove_widget(game)
        game.clear()
        del(game)
        Element.reset()
        self.current = 'main'
        report()

    def report(self):
        report()


class AlcanApp(App):
    def build(self):
        self.sm = AlcanSM()
        return self.sm


if __name__ == '__main__':

    if "DEBUG" in os.environ:
        def debug_signal_handler(signal, frame):
            import pudb
            pudb.set_trace()

        import signal
        signal.signal(signal.SIGINT, debug_signal_handler)

    AlcanApp().run()
