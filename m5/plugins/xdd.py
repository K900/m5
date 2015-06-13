import requests
from m5.core.event.messaging import reply, TARGET_PRIVATE
from m5.plugins.command_dispatcher import command

__author__ = 'K900'

@command('xdd')
def get_word(message):
    """
    Get a random word from a dictionary. Cheesecake, or however the kids these days say it.
    Usage: xdd
    """
    word = requests.get('http://randomword.setgetgo.com/get.php').text.strip().capitalize() + '!'
    reply(word, message, target=TARGET_PRIVATE)