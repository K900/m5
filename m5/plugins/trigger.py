import logging
import re
import peewee
from schema import And, Schema, Optional
from m5.core.dispatcher import on
from m5.core.event.messaging import reply
from m5.util.configuration import load_config, get_database

LOG = logging.getLogger('m5.plugin.trigger')

schema = Schema(
    {
        'trigger': [
            {
                'regex': And(str, len),
                'message': And(str, len),
                Optional('once'): bool
            }
        ]
    }
)

config = load_config('trigger', schema)
db = get_database('trigger')


class Action(peewee.Model):
    identity = peewee.CharField()
    regex = peewee.CharField()
    message = peewee.CharField()

    class Meta:
        database = db

Action.create_table(fail_silently=True)


@on('message')
def trigger(message):
    if config:
        for pair in config['trigger']:
            if re.search(pair['regex'], message.text):
                if pair.get('once', True):
                    i = message.source.identity
                    r = pair['regex']
                    m = pair['message']
                    if Action.select() \
                            .where(Action.identity == i) \
                            .where(Action.regex == r) \
                            .where(Action.message == m).count() == 0:
                        LOG.debug('Sent one-time message to user {}:\n{}'.format(i, m))
                        Action.create(identity=i, regex=r, message=m)
                        reply(pair['message'], message)
                else:
                    reply(pair['message'], message)