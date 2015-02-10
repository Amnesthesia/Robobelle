import re
from bot.module_loader import ModuleLoader
from twisted.python import log


class BaseModule(object):
    matchers = dict({})
    events = dict({})
    timer = dict({})

    def __init__(self, module):
        self.register_module(module)

    def register_module(self, module):
        loader = ModuleLoader()
        if hasattr(module,'matchers') and len(module.matchers):
            for regex,function in module.matchers.items():
                ModuleLoader.register_regex(loader, regex, module, function, getattr(module, function).__doc__)
                log.msg("Module {mod} registered matcher {match} => {func}".format(mod=module.__class__.__name__,match=regex, func=function))
        if hasattr(module,'events') and len(module.events):
            for event, action in module.events.items():
                ModuleLoader.register_event(loader, event, module, action, getattr(module, function).__doc__)
                log.msg("Module {mod} registered for event {ev} => {func}".format(mod=module.__class__.__name__, ev=event, func=function))
        if hasattr(module,'timer') and len(module.timer):
            for seconds, action in module.timer.items():
                ModuleLoader.register_timer(loader, int(seconds), module, action, getattr(module, action).__doc__)
                log.msg("Module {mod} registered for timer {ev}s => {func}".format(mod=module.__class__.__name__, ev=seconds, func=action))
        if hasattr(module, 'raw'):
          ModuleLoader.register_raw(loader, module, getattr(module,'raw').__doc__)
          log.msg("Module {mod} registered raw message processing => {func}".format(mod=module.__class__.__name__, func=function))
