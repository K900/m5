from m5.core import dispatcher
from m5.core.event.messaging import reply
from m5.core.permissions import requires
from m5.plugins.command_dispatcher import command


@command('unload')
@requires('m5.plugin_manager.control')
def unload(data):
    """
    Unload a plugin module by name
    Usage: unload <plugin_module>
    """
    target = data.parsed_args['<plugin_module>']
    if target in dispatcher.modules:
        dispatcher.unload_module(dispatcher.modules[target])
        reply('Done!', data)
    else:
        reply('Module not found!', data)


@command('load')
@requires('m5.plugin_manager.control')
def load(data):
    """
    Load a plugin module by name
    Usage: load <plugin_module>
    """
    try:
        dispatcher.load_module(data.parsed_args['<plugin_module>'])
        reply('Done!', data)
    except ImportError as e:
        reply('Error: {}'.format(e.msg), data)


@command('reload_all')
@requires('m5.plugin_manager.restart')
def reload_all(data):
    """
    Reload all plugin modules
    Usage: reload_all
    """
    for module in dispatcher.modules.values():
        dispatcher.unload_module(module)
    dispatcher.discover()
    reply('Reloaded!', data)