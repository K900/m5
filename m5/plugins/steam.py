import random

from lxml import etree
import requests
from m5.core.event.messaging import reply, TARGET_SAME, TARGET_BROADCAST, TARGET_PRIVATE
from m5.core.permissions import check

from m5.plugins.command_dispatcher import command


@command('random_game')
def random_game(message):
    """
    Get a random game from your Steam Community page
    Usage:
        random_game (-i <id64> | -u <username>)

    -i <id64>, --id=<id64>                   Search by a Steam64 ID
    -u <username>, --username=<username>     Search by a SteamCommunity ('vanity') username
    """

    if message.parsed_args['--username']:
        url = 'http://steamcommunity.com/id/{}/games?xml=1'.format(message.parsed_args['--username'])
    else:
        url = 'http://steamcommunity.com/profiles/{}/games?xml=1'.format(message.parsed_args['--id'])

    data = requests.get(url).text

    et = etree.fromstring(data.encode('utf-8'))

    game = random.choice(et.findall('.//game'))

    name = game.find('name').text
    app_id = game.find('appID').text

    reply('Play {}! steam://run/{}'.format(name, app_id), message, target=TARGET_SAME)


def load_deals():
    _deals = {'daily': [], 'flash': []}

    daily = requests.get('http://store.steampowered.com/api/featured/').json()
    for item in daily['large_capsules']:
        if item['discount_percent']:
            _deals['daily'].append({
                'name': item['name'],
                'discount': item['discount_percent'],
                'id': item['id'],
                'win': 'W' if item['windows_available'] else '',
                'mac': 'M' if item['mac_available'] else '',
                'linux': 'L' if item['linux_available'] else ''
            })

    return _deals


@command('deals')
def deals(message):
    """
    Get the latest deals from Steam
    Usage:
        deals [options]

    -b, --broadcast           Broadcast to channel (admin only)

    """

    if message.parsed_args['--broadcast'] and check(message.source.identity, 'm5.steam.deals.bcast'):
        target = TARGET_BROADCAST
    else:
        target = TARGET_PRIVATE

    deal = '    [{win}{mac}{linux}] {name}: {discount}% off [ steam://advertise/{id} ]\n'
    _deals = load_deals()

    deal_text = "\nDaily deals:\n"
    for item in _deals['daily']:
        deal_text += deal.format(**item)

    deal_text += "Flash sales / community choice:\n"
    for item in _deals['flash']:
        deal_text += deal.format(**item)

    reply(deal_text, message, target=target)