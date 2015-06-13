class Chatroom:
    def send_message(self, message):
        pass


class User:
    identity = None
    chatroom = None

    def send_message(self, message):
        pass


class MessageEventData:
    def __init__(self, text, source, is_broadcast=False):
        self.text = text
        self.source = source
        self.is_broadcast = is_broadcast


class StatusEventData:
    def __init__(self, source):
        self.source = source

TARGET_PRIVATE = 'private'
TARGET_BROADCAST = 'broadcast'
TARGET_SAME = 'same'


def reply(message, event_data, target=TARGET_PRIVATE):
    if target == TARGET_SAME:
        if event_data.is_broadcast and event_data.source.chatroom:
            target = TARGET_BROADCAST
        else:
            target = TARGET_PRIVATE

    if target == TARGET_BROADCAST:
        return event_data.source.chatroom.send_message(message)
    else:
        return event_data.source.send_message(message)