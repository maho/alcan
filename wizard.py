import time

from cymunk import PivotJoint, Vec2d

from anim import AnimObject
import defs


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
        self.parent.num_elements_in_zone -= 1

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
