from m5.core import dispatcher, permissions
from m5.core.event.messaging import Chatroom, MessageEventData, User, StatusEventData

import logging
logging.basicConfig(level=logging.DEBUG, format='<%(levelname)-8s> %(name)-20s: %(message)s')

class ShellChatroom(Chatroom):
    def send_message(self, message):
        print('broadcast:', message)


class ShellUser(User):
    def __init__(self):
        super().__init__()
        self.identity = 'ShellUser'
        self.chatroom = ShellChatroom()

    def send_message(self, message):
        print(message)

u = ShellUser()
dispatcher.fire('joined', StatusEventData(u))
permissions.grant('ShellUser', permissions.SUPERUSER)
dispatcher.discover()

while True:
    text = input('>')
    dispatcher.fire('message', MessageEventData(text, u, False))
    dispatcher.loop()
