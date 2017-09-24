from functools import partial
from random import choice
import re

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.properties import BooleanProperty
from kivy.vector import Vector

from anim import AnimObject
import defs

def load_elmap():
    if load_elmap.data:
        return load_elmap.data
    with open("data/elmap.txt") as f:
        for line in f:
            g = re.match("^(.*)=(.*)\+(.*)$", line)
            if not g:
                continue
            c = g.group(1).strip()
            a = g.group(2).strip()
            b = g.group(3).strip()

            key = tuple(sorted([a,b]))
            assert key not in load_elmap.data, "duplicate combination %s"%key
            load_elmap.data[key] = c

    return load_elmap.data


load_elmap.data = {}

def combine_elements(a, b):

    elmap = load_elmap()

    try:
        return elmap[tuple(sorted([a, b]))]
    except KeyError:
        return None



class Explosion(AnimObject):


    def __init__(self, *a, **kw):
        super(Explosion, self).__init__(*a, **kw)
        self.layers = defs.VISUAL_EFFECTS_LAYER

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
    # is activated when shooted, and then it combine with other element
    activated = BooleanProperty(False)

    #available_elnames = {'water', 'fire'}
    available_elnames = {'water', 'air', 'earth', 'fire'}

    def __init__(self, elname, *a, mass=50, momentum=10, activate=False, **kw):
        self.elname = elname
        super(Element, self).__init__(*a, **kw)
        self.imgsrc = "img/" + elname + ".png"
        self.layers = defs.NORMAL_LAYER
        if activate:
            self.activated = True

    def __repr__(self):
        return "[E:%s id=%s]"%(self.elname, id(self))

    def activate(self, dt=None, timeout=0.5):
        if timeout == 'now':
            self.activated = True
            return

        Clock.schedule_once(partial(self.activate, timeout='now'), timeout)

    def unjoint(self):
        """ remove existing joint """
        if not self.joint:
            return
        joint = self.joint
        self.joint = None
        self.space.remove(joint)
        del(joint)

    def collide_with_another(self, element, dt=None):
        if not element.activated or not self.activated:
            return True

        Logger.debug("collision: %s vs %s (%s vs %s)", self.elname, element.elname, self, element)
        if self.parent is None:
            Logger.debug("hey, my parent is still none, (and me=%s)", self)
            return
        new_elname = combine_elements(self.elname, element.elname)

        if new_elname is None:
            if defs.explode_when_nocomb:
                self.parent.replace_obj(self, Explosion, center=self.center)
                self.parent.remove_obj(element)
            return True

        self.available_elnames.add(new_elname)

        self.parent.replace_obj(self, Element, new_elname, activate=True)
        self.parent.remove_obj(element)

    @classmethod
    def random(cls, **kwargs):
        return Element(elname=choice(list(cls.available_elnames)), **kwargs)

        


