import time

from cymunk import PivotJoint, Vec2d
from kivy.logger import Logger

from anim import AnimObject
import defs


class Wizard(AnimObject):

    collision_type = 3

    def __init__(self, *a, **kw):
        Logger.debug("wizard self=%s", self)
        super(Wizard, self).__init__(*a, mass=defs.wizard_mass, **kw)
        self.layers = defs.NORMAL_LAYER
        self.carried_elements = []
        Logger.debug("wizard=%s and id(self.carried_elements) = %s", self, id(self.carried_elements))
        self.applied_force = Vec2d(0, 0)

    def carry_element(self, element, __dt=None):
        Logger.debug("carry element Wizard=%s element=%s self.carried_elements=%s", 
                self, element, self.carried_elements)
        if time.time() - element.released_at < 1.0:
            return True
        # move element to "carried elements layer"
        element.shape.layers = defs.CARRIED_THINGS_LAYER

        # bind it to wizard
        # #move element up
        pivot = self.body.position + Vec2d(defs.wizard_hand)
        element.body.position = pivot
        element.joint(self, pivot)

        self.carried_elements.append(element)
        Logger.debug("self.carried_elements=%s", self.carried_elements)
        Logger.debug(" in carry_element: wizard=%s and id(self.carried_elements) = %s", self, id(self.carried_elements))
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
        Logger.debug("in release_element:: wizard=%s and id(self.carried_elements) = %s", self, id(self.carried_elements))
        Logger.debug("releasing elements: %s", self.carried_elements)
        for x in self.carried_elements[:]:
            x.body.apply_impulse(defs.wizard_release_impulse)
            x.unjoint()
            x.shape.layers = defs.NORMAL_LAYER
            x.released_at = time.time()

        return True
