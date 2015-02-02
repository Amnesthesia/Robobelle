from BaseModule import BaseModule
from bot.module_loader import ModuleLoader
from bot.modules.ExampleModule import ExampleModule
import re
from time import sleep

class Help(BaseModule):

    matchers = {"!help": "help_message", "!more": "more_help", "!command": "help_command"}
    event = {"join": "say_hi"}
    help = []
    help_msg = []

    def __init__(self, args):
        """
          Initialize the class as a subclass of BaseModule
          and call parent constructor with the defined matchers.
          These will be turned into regex-matchers that redirect to
          the provided function name
        """
        super(self.__class__,self).__init__(self)
        self.create_help_message()

    def help_message(self,msg):
      """ Prints a help message for all commands """
      for line in self.help_msg[:len(self.help_msg)/2]:
        msg.notice(line)
      msg.reply("I've sent my resume your way, {}. For more commands, type !more".format(msg.author))

    def more_help(self,msg):
      """ Prints the second help page """
      for line in self.help_msg[len(self.help_msg)/2:]:
        msg.notice(line)

    def help_command(self,msg):
      """ Prints help for a specific command """
      find_help = [cmdhelp for index, cmdhelp in enumerate(self.help) if cmdhelp[0] == msg.clean_contents.strip()]
      if len(find_help):
        msg.reply(find_help[0][0]+": "+find_help[0][1])
      else:
        msg.reply("Well, that's a trick I don't know ... please don't hate me :(")


    def create_help_message(self):
        """
        Prints a help message generated from docstrings from loaded modules
        """
        self.help = [(re.sub(r'((\\w\**\+*)|(\\s\+*\**)|\^|\\b\**\+*)', '', mod["regex"]), mod["description"].strip('\n')) for mod in ModuleLoader.modules["regex"] ]
        print(self.help)
        self.help = sorted(self.help, key=lambda command: command[0])

        count = 0

        for i,h in enumerate(self.help):
          if h[0] in ExampleModule.matchers.keys():
            continue
          # Remove regex notation (\s*+, \w*+, \b+*)
          if h[0] and h[1]:
            self.help_msg.append("\t" + h[0] + "\t-\t" + h[1].strip())
