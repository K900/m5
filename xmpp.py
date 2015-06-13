import logging
import sys
import threading

from schema import Schema, And, Optional
from sleekxmpp import ClientXMPP

from m5.core import dispatcher, permissions, meta
from m5.core.event.messaging import MessageEventData, Chatroom, User, StatusEventData
from m5.core.permissions import requires
from m5.plugins.command_dispatcher import command
from m5.util.configuration import load_config

users = {}
rooms = {}

LOG = logging.getLogger('m5.xmpp')


class XMPPChatroom(Chatroom):
    def __init__(self, xmpp, room_id):
        self.xmpp = xmpp
        self.room_id = room_id

    def send_message(self, message):
        self.xmpp.send_message(mto=self.room_id, mbody=message, mtype='groupchat')


def jid_to_identity(jid):
    if jid.domain.endswith('xmpp.evolvehq.com'):
        return jid.resource
    else:
        return jid


def get_user(jid):
    if jid.full not in users:
        users[jid.full] = XMPPUser(client, jid)
    return users[jid.full]


class XMPPUser(User):
    def __init__(self, xmpp, jid):
        self.xmpp = xmpp
        self.jid = jid
        self.identity = jid_to_identity(jid)
        self.chatroom = rooms.get(jid.bare, None)

    def send_message(self, message):
        self.xmpp.send_message(mto=self.jid.full, mbody=message, mtype='chat')


logging.basicConfig(level=logging.DEBUG, format='<%(levelname)-8s> %(name)-20s: %(message)s')
# Shut Sleek up
logging.getLogger('sleekxmpp').setLevel(logging.INFO)

# Initialize the dispatcher
dispatcher.discover()

schema = Schema(
    {
        'jid': And(str, len),
        'password': And(str, len),
        Optional('nickname'): And(str, len),
        'rooms': [
            {
                'jid': And(str, len),
                Optional('password'): And(str, len)
            }
        ]
    }
)

config = load_config('xmpp', schema)

nickname = config.get('nickname', 'm5')

client = ClientXMPP(config['jid'], config['password'])

# Enable group chats
client.register_plugin('xep_0045')


# Group chat handlers
def on_muc_online(stanza):
    if stanza['muc']['nick'] != nickname:
        LOG.info('{} joined the room!'.format(stanza['from']))
        user = XMPPUser(client, stanza['from'])
        users[stanza['from'].full] = user

        dispatcher.fire('joined', StatusEventData(user))

        role = stanza['muc']['affiliation']

        if role in ['admin', 'owner']:
            permissions.grant(user.identity, permissions.SUPERUSER)


def on_muc_offline(stanza):
    if stanza['muc']['nick'] != nickname:
        LOG.info('{} left the room!'.format(stanza['from']))
        user = get_user(stanza['from'])
        dispatcher.fire('left', StatusEventData(user))
        del user


def on_muc_message(stanza):
    if stanza['from'].resource:
        if stanza['mucnick'] != nickname:
            dispatcher.fire('message', MessageEventData(
                stanza['body'],
                get_user(stanza['from']),
                True
            ))


client.add_event_handler('groupchat_message', on_muc_message)

# Provide version information
client.register_plugin('xep_0092')
client['xep_0092'].software_name = meta.NAME
client['xep_0092'].version = meta.VERSION
client['xep_0092'].os = sys.platform


# Join all rooms when we're done connecting
def on_start(_):
    client.get_roster()
    client.send_presence(pfrom=config['jid'], pstatus="I'm a bot!")

    for item in config['rooms']:
        LOG.info('Joining {}...'.format(item['jid']))
        client.add_event_handler('muc::{}::got_online'.format(item['jid']), on_muc_online)
        client.add_event_handler('muc::{}::got_offline'.format(item['jid']), on_muc_offline)
        client.plugin['xep_0045'].joinMUC(item['jid'], nick=nickname, password=item.get('password'), wait=True)

        rooms[item['jid']] = XMPPChatroom(client, item['jid'])


client.add_event_handler('session_start', on_start)


# Handle private messages
def on_message(stanza):
    if stanza['type'] == 'chat':
        dispatcher.fire('message', MessageEventData(
            stanza['body'],
            get_user(stanza['from']),
            False
        ))


client.add_event_handler('message', on_message)
client.add_event_handler('ssl_invalid_cert', lambda *args: None)
client.add_event_handler('ssl_expired_cert', lambda *args: None)

LOG.info('Starting message thread...')
t = threading.Thread(target=dispatcher.loop)
t.start()

LOG.info('Connecting...')
client.connect()
dispatcher.fire('xmpp.client_ready', client)
LOG.info('Connected!')


@command('stop')
@requires(permissions.SUPERUSER)
def stop(_):
    dispatcher.fire('stop', None)
    client.disconnect()


LOG.info('Starting event loop...')
client.process()