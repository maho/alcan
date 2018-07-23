import logging
# from logging.handlers import DatagramHandler
# from logging.handlers import SysLogHandler
import weakref

from kivy.logger import Logger

import defs

def adhoco(**kwargs):
    return type('adhoc_object', (object,), dict(**kwargs))

# def observe(obj):
#     try:
#         observe.objs.append((weakref.ref(obj), str(obj)))
#     except TypeError:
#         Logger.warning("unable to observe %s"%obj)
#     return obj
# observe.objs = []

# def report():
#     for o, d in observe.objs:
#         if o() is not None:
#             Logger.info("(%s) is dead"%d)
#         else:
#             Logger.info("(%s) is still alive"%d)


def configure_logger():
    pass
#     # h = SysLogHandler(address=defs.syslog_host)
#     h = DatagramHandler(*defs.syslog_host)
#     h.setLevel(logging.DEBUG)
# 
#     rlogg = logging.getLogger()
#     rlogg.addHandler(h)
#     rlogg.setLevel(logging.DEBUG)
# 
#     logging.info("das ist info")
#     logging.debug("eta diebug")
# 
#     Logger.info("a eta kivy's info")
