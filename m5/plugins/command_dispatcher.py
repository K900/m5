import functools
import logging
import shlex

import docopt

from m5.core import dispatcher
from m5.core.dispatcher import on
from m5.core.event.messaging import MessageEventData, reply

commands = {}

LOG = logging.getLogger('m5.plugin.command_dispatcher')


class CommandEventData(MessageEventData):
    def __init__(self, text, source, is_broadcast=False, args=None):
        if not args:
            args = []

        super().__init__(text, source, is_broadcast)
        self.args = args


@on('message')
def dispatch(message):
    text = message.text
    if text.startswith('.'):
        spl = shlex.split(text[1:])
        if spl:
            name, *args = spl
            LOG.debug('Firing command {} with arguments {}'.format(name, ', '.join(args)))
            dispatcher.fire('command:{}'.format(name), CommandEventData(
                message.text,
                message.source,
                message.is_broadcast,
                args
            ))


class DuplicateCommandWarning(Warning):
    pass


def command(*names):
    if not names:
        raise ValueError('At least one name must be provided for the command!')

    def command_decorator(fn):
        if fn.__doc__:
            LOG.debug('Monkey-patching docopt into command handler for {}'.format(names[0]))

            @functools.wraps(fn)
            def wrapper(data):
                try:
                    data.parsed_args = docopt.docopt(fn.__doc__, data.args, help=False, version=False)
                except docopt.DocoptExit as e:
                    return reply(e.usage, data)
                return fn(data)

            if hasattr(fn, '__m5_permissions__'):
                LOG.debug('Docopt added after permissions, copied permission information')
                wrapper.__m5_permissions__ = fn.__m5_permissions__
        else:
            wrapper = fn

        wrapper.__m5_aliases__ = names

        LOG.debug('Registering handler {} for commands {}'.format(wrapper, ', '.join(names)))
        for name in names:
            event = 'command:{}'.format(name)
            if dispatcher.handlers[event]:
                LOG.warning('Multiple handlers registered for command {}'.format(name), stacklevel=2)
            dispatcher.register(event, wrapper)

        commands[names[0]] = wrapper

        return wrapper

    return command_decorator