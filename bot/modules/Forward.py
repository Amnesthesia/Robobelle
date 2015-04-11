from BaseModule import BaseModule
from bot.module_loader import ModuleLoader

class Forward(BaseModule):

    matchers = {"!forward": "forward"}

    def __init__(self, args):
        """
          Initialize the class as a subclass of BaseModule
          and call parent constructor with the defined matchers.
          These will be turned into regex-matchers that redirect to
          the provided function name
        """
        super(self.__class__,self).__init__(self)

    def forward(self,msg):
        """
        Forwards the text to a channel or user. Arguments: #channel message
        """
        split_msg = msg.clean_contents.split(" ")

        channel = split_msg.pop(0)
        msg = " ".join(split_msg)

        ModuleLoader().reply_handle.msg(channel, msg)

        return msg
