from arrow import Arrow
from m5.core.dispatcher import on
from m5.core.event.messaging import reply
from m5.core.meta import VERSION_STRING
from m5.plugins.command_dispatcher import command

try:
    # noinspection PyUnboundLocalVariable,PyUnresolvedReferences
    uptime
except NameError:
    uptime = Arrow.now()

try:
    # noinspection PyUnboundLocalVariable
    crash_count
except NameError:
    crash_count = 0

code_uptime = Arrow.now()


@on('crash')
def crash(_):
    global crash_count
    crash_count += 1


@command('uptime')
def get_uptime(message):
    """
    Get uptime, code reload time and crash counts this session
    Usage: uptime
    """
    now = Arrow.now()
    reply('''{}

Way status:
    [ ] Lost
    [X] Not lost

Holding on since:
    {}
Uptime:
    {}
Last code reload:
    {}
Code uptime:
    {}

Total crashes this session: {}
    '''.format(
        VERSION_STRING,
        uptime.humanize(),
        now - uptime,
        code_uptime.humanize(),
        now - code_uptime,
        crash_count
    ), message)
