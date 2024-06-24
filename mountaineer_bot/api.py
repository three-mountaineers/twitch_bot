import requests

def check_channel_is_live(channel: str):
    contents = requests.get(f'https://www.twitch.tv/{channel}').content.decode('utf-8')
    return 'isLiveBroadcast' in contents