import weakref

from kivy.logger import Logger

def adhoco(**kwargs):
    return type('adhoc_object', (object,), dict(**kwargs))

def observe(obj):
    try:
        observe.objs.append((weakref.ref(obj), str(obj)))
    except TypeError:
        Logger.warning("unable to observe %s"%obj)
    return obj
observe.objs = []

def report():
    for o, d in observe.objs:
        if o() is not None:
            Logger.info("(%s) is dead"%d)
        else:
            Logger.info("(%s) is still alive"%d)


