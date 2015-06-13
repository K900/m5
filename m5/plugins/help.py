from m5.core import permissions
from m5.core.event.messaging import reply
from m5.plugins import command_dispatcher
from m5.plugins.command_dispatcher import command

plugin_pages = {}


def _remove_indent(s):
    lines = s.split('\n')
    all_lines = []
    indent = None
    for line in lines:
        ls = line.strip()
        if ls:
            indent = len(line) - len(ls)
            break
    all_lines += ['    ' + l[indent:] for l in lines]

    if not all_lines[0].strip():
        all_lines.pop(0)

    return '\n'.join(all_lines)


@command('help', '?')
def cmd_help(message):
    """
    Get help for commands and plugins
    Usage: help [<object>]...
    """
    lines = []

    targets = message.parsed_args['<object>'] or (list(command_dispatcher.commands.keys()) + list(plugin_pages.keys()))

    for command_name in targets:
        if command_name in command_dispatcher.commands:
            command_handler = command_dispatcher.commands[command_name]
            if hasattr(command_handler, '__m5_permissions__'):
                if not permissions.check(message.source.identity, command_handler.__m5_permissions__):
                    continue
            lines.append('Help for command {} (aliases: {}):'.format(
                command_name,
                ', '.join(command_handler.__m5_aliases__))
            )
            if command_handler.__doc__:
                lines.append(_remove_indent(command_handler.__doc__))
            else:
                lines.append('    No help message :(\n')
        elif command_name in plugin_pages:
            lines.append('Help for plugin {}:'.format(command_name))
            lines.append(_remove_indent(plugin_pages[command_name]))
        else:
            lines.append('Unknown command or plugin: {}!'.format(command_name))

    reply('\n'.join(lines), message)
