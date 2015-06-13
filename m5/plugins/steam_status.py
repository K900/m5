import requests
from m5.core.event.messaging import reply, TARGET_SAME
from m5.plugins.command_dispatcher import command


@command('steam_status', 'sup')
def steam_status(message):
    """
    Gets the status for Steam services

    Usage: steam_status [--short]
    """

    data = requests.get('http://steamdb.info/api/SteamRailgun').json()
    if message.parsed_args['--short']:
        states = [data['services'][x]['status'] == 'good' for x in data['services']]
        if all(states):
            reply('All Steam servers are online!', message, target=TARGET_SAME)
        else:
            reply('Some Steam servers are offline, .steam_status for more', message, target=TARGET_SAME)
    else:
        flags = {x: data['services'][x]['title'] for x in data['services']}
        reply('''Current Steam service status:
Main servers: {steam}
Store: {store}
Community: {community}
Dota 2: {dota2}
Team Fortress 2: {tf2}
CS: GO: {csgo}
Online: {online}'''.format(**flags), message, target=TARGET_SAME)
