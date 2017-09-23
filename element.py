from functools import partial
from random import shuffle

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.vector import Vector

from anim import AnimObject
import defs

elmap = {
        ('water', 'fire'): 'steam'
    }

def combine_elements(a, b):
    try:
        return elmap[a, b]
    except KeyError:
        return None



class Explosion(AnimObject):

    layers = defs.VISUAL_EFFECTS_LAYER

    def __init__(self, *a, **kw):
        super(Explosion, self).__init__(*a, **kw)

    def update(self, dt):
        if self.parent is None:
            Logger.info("self=%s self.parent=%s self.frame=%s but parent is None", self, self.parent, self.frame)
            return
        if self.frame > 5:
            self.parent.remove_obj(self)
            return
        self.frame += 1

        #dirty hack, how to do it otherwise?
        oldsize = sum(self.size)/2
        size = (100*(5 - self.frame) + 18*(self.frame-1))/4
        ds = oldsize - size
        self.size = (size, size)
        self.pos = Vector(self.pos) + (ds/2, ds/2)

       






class Element(AnimObject):
    collision_type = 1
    layers = defs.NORMAL_LAYER

    available_elnames = {'water', 'fire', 'earth', 'air'}

    def __init__(self, elname, *a, mass=50, momentum=10, **kw):
        super(Element, self).__init__(*a, **kw)
        self.elname = elname
        self.imgsrc = "img/" + elname + ".png"

    def unjoint(self):
        """ remove existing joint """
        if not self.joint:
            return
        joint = self.joint
        self.joint = None
        self.space.remove(joint)
        del(joint)

    def collide_with_another(self, element, dt=None):
        if self.parent is None:
            Logger.debug("hey, my parent is still none, (and me=%s)", self)
            return
        new_elname = combine_elements(self.elname, element.elname)
        if new_elname is None:
            self.parent.replace_obj(self, Explosion(center=self.center))
            self.parent.remove_obj(element)
            return

        self.available_elnames.add(new_elname)

        self.parent.replace_obj(self, Element(new_elname, center=self.center))

    @classmethod
    def random(cls):
        return Element(elname=shuffle(cls.available_elnames))

        


