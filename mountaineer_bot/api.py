import requests
import logging
import json

from mountaineer_bot import windows_auth, twitch_auth
from mountaineer_bot.twitchauth import core

def check_channel_is_live(channel: str):
    contents = requests.get(f'https://www.twitch.tv/{channel}').content.decode('utf-8')
    return 'isLiveBroadcast' in contents

def get_user_id(cfg_dict: dict, username: str):
    access_token = windows_auth.get_access_token(cfg_dict, cfg_dict['CLIENT_ID'])
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-Id": cfg_dict['CLIENT_ID'],
        "Content-Type": "application/json",
    }
    r = requests.get(
        url = "https://api.twitch.tv/helix/users",
        headers = headers,
        params={
            'login': username,
        }
    )
    if r.status_code >= 400:
        if 'Invalid OAuth token' in r.content.decode('utf-8'):
            core.refresh_token(cfg_dict)
            return get_user_id(cfg_dict=cfg_dict, username=username)
        raise RuntimeError(r.content)
    else:
        payload = json.loads(r.content)
        return payload["data"][0]["id"]