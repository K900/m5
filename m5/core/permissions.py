import functools
import logging
from m5.core.dispatcher import on
from m5.core.event.messaging import reply

SUPERUSER = 'm5.superuser'
LOG = logging.getLogger('m5.permissions')

_permissions = {}


class UnknownIdentity(Exception):
    pass


def _ensure_registered(fn):
    @functools.wraps(fn)
    def wrapper(identity, *args, **kwargs):
        if identity not in _permissions:
            register(identity)
        return fn(identity, *args, **kwargs)

    return wrapper


@on('joined')
def _auto_register(data):
    LOG.debug('Caught join event, auto-creating permission sets...')
    register(data.source.identity)


def register(identity):
    LOG.debug('Creating new permission set for identity {}'.format(identity))
    if identity not in _permissions:
        _permissions[identity] = set()


@_ensure_registered
def forget(identity):
    LOG.debug('Removing permission set for identity {}'.format(identity))
    del _permissions[identity]


@_ensure_registered
def grant(identity, permission):
    LOG.debug('Granting permission {} to identity {}'.format(permission, identity))
    _permissions[identity].add(permission)


@_ensure_registered
def revoke(identity, permission):
    LOG.debug('Revoking permission {} from identity {}'.format(permission, identity))
    _permissions[identity].remove(permission)


@_ensure_registered
def check(identity, *permissions):
    if SUPERUSER in _permissions[identity]:
        LOG.debug('Verifying all permissions to identity {}, as they are a superuser'.format(identity))
        return True
    else:
        for required_permission in permissions:
            if required_permission not in _permissions[identity]:
                LOG.debug('Not verifying permission {} for identity {}'.format(required_permission, identity))
                return False
        LOG.debug('Verifying permissions {} for identity {}'.format(', '.join(permissions), identity))
        return True


@_ensure_registered
def list_all(identity):
    return _permissions[identity]


def requires(*permissions):
    def require_decorator(fn):
        if hasattr(fn, '__m5_permissions__'):
            fn.__m5_permissions__.update(*permissions)
            return fn

        @functools.wraps(fn)
        def require_wrapper(message):
            if check(message.source.identity, require_wrapper.__m5_permissions__):
                return fn(message)
            else:
                return reply('No permission!', message)

        require_wrapper.__m5_permissions__ = set(permissions)

        return require_wrapper

    return require_decorator
