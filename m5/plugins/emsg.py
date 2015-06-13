from m5.core import permissions
from m5.core.dispatcher import on
from m5.core.event.messaging import reply
from m5.core.permissions import requires
from m5.plugins.command_dispatcher import command

try:
    client
except NameError:
    client = None


@on('xmpp.client_ready')
def set_client(_client):
    global client
    client = _client


@command('epm')
@requires(permissions.SUPERUSER)
def epm(message):
    """
    PM a user that you don't have on your friend list
    Usage:
        epm <username> <text>...
    """

    if not client:
        reply('Client not ready, this should not be happening!', message)
        return

    text = ' '.join(message.parsed_args['<text>'])
    client.send_message(mto='{}@xmpp.evolvehq.com'.format(message.parsed_args['<username>']), mbody=text, mtype='chat')
    reply('Sent!', message)