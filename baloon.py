from cymunk import DampedSpring
from kivy.clock import Clock
from kivy.properties import ListProperty, StringProperty

from anim import AnimObject
import defs


class Baloon(AnimObject):

    anchor = ListProperty([0, 0])
    text = StringProperty("...")

    def __init__(self, object_to_follow, center, text, size=(100, 50)):
        super(Baloon, self).__init__(center=center, size=size)

        self.object_to_follow = object_to_follow
        self.anchor = self.object_to_follow.center
        self.layers = defs.VISUAL_EFFECTS_LAYER
        self.text = text

        Clock.schedule_once(self.remove, 5)

    def add_body(self, dt=None):
        super(Baloon, self).add_body(dt=dt)
        if self.body:  # if obj is initialized yet
            gx, gy = defs.gravity
            self.body.apply_force((0, 7500))

            self.joint = DampedSpring(self.body, self.object_to_follow.body,
                                      tuple(self.pos),
                                      tuple(self.object_to_follow.center),
                                      130, 1.9, 1.5)
            self.space.add(self.joint)

    def update(self, dt):
        self.anchor = self.object_to_follow.center

    def remove(self, dt=None):
        """ remove existing joint """
        if not self.joint:
            return
        joint = self.joint
        self.joint = None
        self.space.remove(joint)
        del(joint)

        self.parent.remove_obj(self)
