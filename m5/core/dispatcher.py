import collections
import importlib
import inspect
import logging
import pkgutil
import queue

LOG = logging.getLogger('m5.dispatcher')


class HandlerWrapper:
    def __init__(self, handler):
        self.handler = handler
        self.__doc__ = handler.__doc__
        self.module = inspect.getmodule(handler)

    def __call__(self, *args, **kwargs):
        self.handler(*args, **kwargs)


modules = {}
handlers = collections.defaultdict(list)


def register(event, handler):
    wrapper = HandlerWrapper(handler)
    handlers[event].append(wrapper)
    LOG.debug('Registered handler {} for event {}'.format(handler, event))


def on(event):
    def on_decorator(fn):
        register(event, fn)
        return fn

    return on_decorator


def unregister(handler):
    for event in handlers:
        event.remove(handler)
    LOG.debug('Unregistered handler {} for all events'.format(handler))


class EmptyEventWarning(Warning):
    pass


def unload_module(module):
    LOG.info('Attempting to unload module {}'.format(module))
    for name, event in handlers.items():
        new_events = []
        for e in event:
            if e.module == module:
                LOG.debug('Unloading module hooks for event {}'.format(name))
            else:
                new_events.append(e)
        event[:] = new_events

    LOG.info('Success!')


def load_module(module_name):
    if module_name in modules:
        LOG.info('Attempting to reload existing module {}'.format(module_name))
        unload_module(modules[module_name])
        importlib.reload(modules[module_name])
        LOG.info('Success!')
    else:
        LOG.info('Attempting to load unknown module {}'.format(module_name))
        modules[module_name] = importlib.import_module('m5.plugins.{}'.format(module_name))
        LOG.info('Success!')


def discover():
    LOG.info('Starting module auto-discovery...')
    for _, module_name, is_package in pkgutil.iter_modules(['m5/plugins']):
        if not is_package:
            LOG.info('Module {} discovered, loading'.format(module_name))
            load_module(module_name)


q = queue.Queue()


def fire(event, data):
    LOG.debug('Queueing up event {}, data: {}'.format(event, data))
    q.put((event, data))


def loop(once=False):
    LOG.info('Starting message loop...')
    while not q.empty() if once else True:
        if q.empty():
            continue

        event, data = q.get()
        if event == 'stop':
            return

        LOG.debug('Firing event {}'.format(event))
        if handlers[event]:
            for handler in handlers[event]:
                # noinspection PyBroadException
                try:
                    LOG.debug('Calling event handler {} for event {}...'.format(handler.handler, event))
                    handler(data)
                except Exception:
                    fire('crash', None)
                    LOG.exception('Event handler {} failed for event {}!'.format(handler.handler, event))
        else:
            LOG.debug('Attempted to fire event {} with no handlers attached'.format(event))