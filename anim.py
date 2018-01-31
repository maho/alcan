from math import degrees

from cymunk import Body, Circle, Space, Segment, Vec2d
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget

import defs
from utils import observe as obs


class PhysicsObject(object):
    """ super object, which holds physics in class attributes """

    space = None
    bodyobjects = {}

    mass = NumericProperty(10, allownone=True)
    momentum = NumericProperty('INF', allownone=True)
    friction = NumericProperty(defs.friction)

    def __init__(self):
        if self.space is None:
            self.init_physics()

    @staticmethod
    def init_physics():
        """ instead of using space as global variable """
        cls = PhysicsObject
        cls.space = obs(Space())
        cls.space.gravity = defs.gravity

        ra = 100
        w, h = defs.map_size

        for x1, y1, x2, y2, ct in [
                (-100, defs.floor_level - ra, w + 100, defs.floor_level - ra, defs.BOTTOM_BOUND),
                (-ra, h + 100, -ra, -100, defs.LEFT_BOUND),
                (w + ra, h + 100, w + ra, -100, defs.RIGHT_BOUND)
              ]:
            wall = Segment(cls.space.static_body, Vec2d(x1, y1), Vec2d(x2, y2), ra)
            wall.elasticity = 0.6
            wall.friction = defs.friction
            wall.collision_type = ct
            cls.space.add_static(obs(wall))

    @staticmethod
    def del_physics():
        cls = PhysicsObject
        del(cls.space)
        cls.space = None

    @classmethod
    def update_space(cls):
        cls.space.step(1.0/20.0)

        for __b, o in cls.bodyobjects.items():
            o.update_to_body()

    def add_to_space(self, __body, space):
        space = self.space

        if self.mass is not None:
            space.add(self.body)

        space.add(self.shape)

        self.bodyobjects[self.body] = self

        self.on_body_init()

    def update_to_body(self):
        """
            update widget position to body position
        """
        p = self.body.position
        self.center = tuple(p)

        if hasattr(self, 'angle'):
            ang = degrees(self.body.angle)
            self.angle = ang

    def on_body_init(self):
        """ called when body is finally set up """
        pass

class ClockStopper(Widget):
    """ class which holds all scheduled clocks and allows to stop them all
        useful if it's eg. game over """

    clocks = []
    
    def __init__(self, *args, **kwargs):
        self.on_init_called = False
        super(ClockStopper, self).__init__(*args, **kwargs)
        self.wait_for_parent()

    def wait_for_parent(self, dt=None):
        if self.parent and not self.on_init_called:
            # finally
            self.on_init()
            self.on_init_called = True
            return

        self.schedule_once(self.wait_for_parent)

    def on_init(self):
        pass

    @classmethod
    def schedule_once(cls, *args, **kwargs):
        cls.clocks.append(Clock.schedule_once(*args, **kwargs))
        cls.clocks_cleanup()

    @classmethod
    def schedule_interval(cls, *args, **kwargs):
        cls.clocks.append(Clock.schedule_interval(*args, **kwargs))
        cls.clocks_cleanup()

    @classmethod
    def stop_all_clocks(cls):
        for event in cls.clocks:
            event.cancel()
        cls.clocks_cleanup()

    @classmethod
    def clocks_cleanup(cls):
        for ev in cls.clocks[:]:
            if not ev.is_triggered:
                cls.clocks.remove(ev)


class AnimObject(ClockStopper, PhysicsObject):
    """ base object for all animated objects in game """

    collision_type = NumericProperty(0)

    def __init__(self, *args, **kwargs):
        super(AnimObject, self).__init__(*args, **kwargs)

        self.body = None
        self.layers = None
        self.add_body()
        obs(self)

    def add_body(self, dt=None):

        if not self.parent:  # object not initialized yet
            # call myself in next frame,
            self.schedule_once(self.add_body)
            return

        if self.mass is None:
            self.momentum is None

        self.body = Body(self.mass, self.momentum)
        self.body.position = self.center

        self.shape = self.create_shape()

        self.add_to_space(self.body, self.shape)
        obs(self.body)
        obs(self.shape)

    def create_shape(self):
        sx, sy = self.size
        radius = (sx + sy)/4  # half of avg
        shape = Circle(self.body, radius)
        shape.elasticity = 0.6
        shape.friction = self.friction
        shape.collision_type = self.collision_type
        if self.layers:
            shape.layers = self.layers

        return shape

    def before_removing(self):
        """ method called before removing by parent """
        pass

    def show_baloon(self, text, **kwargs):
        from baloon import Baloon
        px, py = self.pos
        if py > 400:
            py = 400
        else:
            py += 200
        self.parent.add_widget(
            obs(Baloon(self, (px, py), text, **kwargs))
        )

    def update(self, dt):
        pass
