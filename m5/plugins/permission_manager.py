from m5.core import permissions
from m5.core.event.messaging import reply
from m5.core.permissions import requires
from m5.plugins.command_dispatcher import command


@command('grant')
@requires(permissions.SUPERUSER)
def grant(message):
    """
    Grant a permission to a user (defaults to m5.superuser)
    Usage: grant <nickname> [<permission>]
    """
    perm = message.parsed_args['<permission>'] or permissions.SUPERUSER
    try:
        permissions.grant(message.parsed_args['<nickname>'], perm)
        reply('Done!', message)
    except permissions.UnknownIdentity:
        reply('Unknown username or identity!', message)


@command('revoke')
@requires(permissions.SUPERUSER)
def revoke(message):
    """
    Revoke a permission from a user
    Usage: revoke <nickname> <permission>
    """
    try:
        permissions.revoke(message.parsed_args['<nickname>'], message.parsed_args['<permission>'])
        reply('Done!', message)
    except permissions.UnknownIdentity:
        reply('Unknown username or identity!', message)


@command('list_permissions')
@requires(permissions.SUPERUSER)
def list_permissions(message):
    """
    List a user's permissions
    Usage: list_permissions <nickname>
    """
    try:
        reply('Permissions list:\n' + '\n'.join(permissions.list_all(message.parsed_args['<nickname>'])), message)
    except permissions.UnknownIdentity:
        reply('Unknown username or identity!', message)