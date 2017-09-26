from cymunk import Body, Circle, Space, Segment, Vec2d
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget

import defs


class PhysicsObject(object):
    """ super object, which holds physics in class attributes """

    space = None
    bodyobjects = {}

    mass = NumericProperty(10, allownone=True)
    momentum = NumericProperty('INF', allownone=True)

    def __init__(self):
        if self.space is None:
            self.init_physics()

    @staticmethod
    def init_physics():
        """ instead of using space as global variable """
        cls = PhysicsObject
        cls.space = Space()
        cls.space.iterations = 60
        cls.space.gravity = defs.gravity

        ra = 100
        w, h = defs.map_size

        for x1, y1, x2, y2 in [(-100, defs.floor_level - ra, w + 100, defs.floor_level - ra),
                               (-ra, w + 100, -ra, -100),
                               (w + ra, w + 100, w + ra, -100)
                               ]:
            wall = Segment(cls.space.static_body, Vec2d(x1, y1), Vec2d(x2, y2), ra)
            wall.elasticity = 0.6
            wall.friction = defs.friction
            cls.space.add_static(wall)

    @classmethod
    def update_space(cls):
        cls.space.step(1.0/20.0)

        for b, o in cls.bodyobjects.items():
            o.update_to_body()

    def add_to_space(self, body, space):
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

    def on_body_init(self):
        """ called when body is finally set up """

#        if self.center_y < defs.kill_level:
#            self.out_of_bounds()
#
#    def out_of_bounds(self):
#        del(self.bodyobjects[self.body])
#        self.space.remove(self.body)
#        self.space.remove(self.shape)
#        self.parent.remove_widget(self)


class AnimObject(Widget, PhysicsObject):
    """ base object for all animated objects in game """

    collision_type = NumericProperty(0)

    def __init__(self, *args, **kwargs):
        super(AnimObject, self).__init__(*args, **kwargs)

        self.body = None
        self.layers = None
        self.add_body()

    def add_body(self, dt=None):

        if not self.parent:  # object not initialized yet
            # call myself in next frame,
            Clock.schedule_once(self.add_body)
            return

        if self.mass is None:
            self.momentum is None

        self.body = Body(self.mass, self.momentum)
        self.body.position = self.center

        self.shape = self.create_shape()

        self.add_to_space(self.body, self.shape)

    def create_shape(self):
        sx, sy = self.size
        radius = (sx + sy)/4  # half of avg
        shape = Circle(self.body, radius)
        shape.elasticity = 0.6
        shape.friction = defs.friction
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
            Baloon(self, (px, py), text, **kwargs)
        )

    def update(self, dt):
        pass
