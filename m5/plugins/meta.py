import datetime
import re
import logging
import urllib.parse

import isodate
import requests

from m5.core.dispatcher import on
from m5.core.event.messaging import reply, TARGET_SAME

YOUTUBE_API_KEY = "AIzaSyCGl9L2uRkZfces3fCWShLt3G-cJq4rmSs"
LOG = logging.getLogger('m5.plugin.meta')

def youtube_loader(url, query):
    youtube_url = 'https://www.googleapis.com/youtube/v3/videos?id={}&key={}&part=snippet,contentDetails'

    blacklist = {
        '1kf-rGHHxsY': 'jumpscare/loud noise',
        '_RO-qdp31cA': 'NSFW'
    }

    if url.path.lower() == '/watch' and 'v' in query:
        vid = query['v'][0]
        url = youtube_url.format(vid, YOUTUBE_API_KEY)
        data = requests.get(url).json()['items'][0]
        title = data['snippet']['title']
        author = data['snippet'].get('channelTitle', '[unknown]')
        duration = isodate.parse_duration(data['contentDetails']['duration'])
        warning = ' warning: ' + blacklist[vid] if vid in blacklist else ''
        return 'YouTube video: {} by {} [{}]{}'.format(title, author, duration, warning)


def vimeo_loader(url, _):
    vimeo_url = 'http://vimeo.com/api/v2/video/{}.json'
    url_path = url.path.strip('/')

    if url_path.isdigit():
        data = requests.get(vimeo_url.format(url_path)).json()[0]
        return 'Vimeo video: {} by {} [{}]'.format(
            data['title'],
            data['user_name'],
            datetime.timedelta(seconds=data['duration'])
        )


def twitch_loader(url, _):
    twitch_url = 'https://api.twitch.tv/kraken/streams/{}'
    stream_url = url.path.strip('/').split('/')[0]
    data = requests.get(twitch_url.format(stream_url)).json()['stream']
    if data:
        stream_name = data['channel'].get('display_name', stream_url)
        status = data['channel'].get('status', '')
        if status:
            status = ' // ' + status
        return 'Twitch.tv stream: {} playing {}{}'.format(stream_name, data['game'] or 'something', status)
    else:
        return 'Twitch.tv: {} is not streaming right now'.format(stream_url)


loaders = {
    'youtube.com': youtube_loader,
    'vimeo.com': vimeo_loader,
    'twitch.tv': twitch_loader
}

try:
    # noinspection PyUnresolvedReferences
    from m5.plugins import help
    help.plugin_pages['meta'] = '''
    Automatically inserts metadata for links to some websites.
    Currently supported domains: {}
    '''.format(', '.join(loaders.keys()))
except ImportError:
    pass


@on('message')
def on_message(message):
    links = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.text)
    for link in links:
        url = urllib.parse.urlparse(link)
        query = urllib.parse.parse_qs(url.query)
        for domain, loader in loaders.items():
            if domain in url.netloc:
                # noinspection PyBroadException
                try:
                    result = loader(url, query)
                    if result:
                        reply(result, message, target=TARGET_SAME)
                        break
                except Exception:
                    LOG.exception('Loader for {} failed!'.format(domain))
                    continue



