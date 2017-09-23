from cymunk import Body, Circle, Space, Segment, Vec2d
from kivy.clock import Clock
from kivy.properties import NumericProperty, ObjectProperty
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

        radius = 100

        cls.floor = Segment(cls.space.static_body, Vec2d(-1000, defs.floor_level - radius), Vec2d(5000, defs.floor_level - radius), radius)
        cls.floor.elasticity = 0.6
        cls.floor.friction = defs.friction
        cls.space.add_static(cls.floor)

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

    def update_to_body(self):
        p = self.body.position
        self.center = tuple(p)

#        if self.center_y < defs.kill_level:
#            self.out_of_bounds()
#
#    def out_of_bounds(self):
#        del(self.bodyobjects[self.body])
#        self.space.remove(self.body)
#        self.space.remove(self.shape)
#        self.parent.remove_widget(self)

        



class AnimObject(Widget, PhysicsObject):

    collision_type = NumericProperty(0)
    layers = None

    def __init__(self, *args, **kwargs):
        super(AnimObject, self).__init__(*args, **kwargs)
        
        self.body = None
        self.add_body()

    def add_body(self, dt=None):

        if not self.parent: #object not initialized yet
            #call myself in next frame, 
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
        radius = (sx + sy)/4 #half of avg
        shape = Circle(self.body, radius)
        shape.elasticity = 0.6
        shape.friction = defs.friction
        shape.collision_type = self.collision_type
        if self.layers:
            shape.layers = self.layers

        return shape

    def update(self, dt):
        pass

