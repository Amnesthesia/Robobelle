import pkgutil
import os
import sys
import re
import copy
from ConfigParser import ConfigParser
from twisted.internet import task
from singleton import Singleton


class ModuleLoader(object):
    """
    Loads all modules dropped into the modules/ folder, using baseclass
    BaseModule. These are stored in modules, which is effectively static.

    Can be accessed anywhere by ModuleLoader.modules
    """
    # Reply handle is used to access Robobelle and send messages without
    # receiving one
    reply_handle = None
    # Contains list of enabled modules
    ENABLED_MODULES = []
    # Contains instances of each module
    modules = dict({
                    "regex": list(),
                    "event": dict({
                                    "kicked": list(),  # When a user is kicked
                                    "joined": list(),  # When a user joined
                                    "parted": list(),  # When a user parted
                                    "topic": list(),    # When topic is changed
                                    "quit": list(),     # When a user quits
                                    "action": list(),   # When a user uses /me
                                    "mode": list(),     # When the mode is changed
                                    "nick": list()   # When a user changed nick
                        }),
                      "timer": list(),
                      "raw": list()
                    })
    __metaclass__ = Singleton

    def __init__(self):
        if not len(self.ENABLED_MODULES):
            self.parse_module_configuration()

        self.load_modules(self.ENABLED_MODULES)

    def parse_module_configuration(self):
        """
        Reads configuration and enables modules
        """
        config = ConfigParser()
        config.read(["settings.ini"])
        self.ENABLED_MODULES = filter(None, list(module.strip() for module in config.get('belle', 'modules').split('\n')))

    def register_regex(self, regex, module, function, description):
        """
        Registers a function to be run on a module when a message
        matches the regex.

        regex   --  Regex to match against
        module  --  Object to run function on
        function    --  Function to run
        description --  Help message to output when !help command is received
        """
        ModuleLoader.modules["regex"].append(dict({"regex": regex, "module": module, "function": function, "description": description}))

    def register_timer(self, timer, module, function, description):
        """
        Registers a function to be run on a module when a message
        matches the regex.

        :param timer:     Seconds between calls
        :param module:    Object to run function on
        :param function:  Function to run
        :param description:  Help message to output when !help command is received
        """
        timer_call = task.LoopingCall(getattr(module,function))
        timer_call.start(timer)
        ModuleLoader.modules["timer"].append(dict({"timer": timer, "module": module, "function": function, "description": description, "handle": timer_call}))



    def register_event(self, event, module, function, description):
        """
        Registers a function to be run on a module when a specific event occurs.

        Existing events are:
            - action [A user performs an action, i.e /me dances]
            - kicked [A user is kicked]
            - joined [A user has joined]
            - mode   [Channel mode is changed]
            - parted [A user has left the channel]
            - quit   [A user has quit the network]
            - renamed[A user changed nick]
            - topic  [Channel topic is changed]

        """
        if event not in module.events.keys():
            raise Exception("Attempt to register event {ev} for {mod} failed. Event not supported.".format(ev=event, mod=module.__class__.__name__))
        else:
            ModuleLoader.modules["event"][event].append(dict({"module": module, "function": function, "description": description}))

    def register_raw(self, module, description):
      """
      Registers modules with a function that should be run on *every*
      message (like checking for URLs, or markov learning)
      """
      ModuleLoader.modules["raw"].append(dict({"module": module, "description": description}))

    def load_modules(self, enabled_modules=[]):
        """
        Loads all modules and assigns them to indexes in ModuleLoader.modules

        Returns dict of module categories
        """
        if not len(enabled_modules) and len(self.ENABLED_MODULES):
            enabled_modules = self.ENABLED_MODULES

        path = os.path.join(os.path.dirname(__file__), "modules")
        modules = pkgutil.iter_modules(path=[path])
        sys.path.append(path)

        for loader, mod_name, ispkg in modules:
            # Ensure that module isn't already loaded
            if mod_name not in sys.modules:
                # Import module
                loaded_mod = __import__(mod_name, fromlist=[mod_name])

                loaded_class = getattr(loaded_mod, mod_name)

                # Create an instance of the class
                # except if it's the BaseModule class
                if mod_name != "BaseModule" and mod_name in self.ENABLED_MODULES:
                    instance = loaded_class(mod_name)
                    # ModuleLoader.modules.append(copy.copy(instance))
                    # log.msg("Loaded module {}".format(mod_name))
                else:
                    print("Module "+mod_name+" not in "+str(self.ENABLED_MODULES))
