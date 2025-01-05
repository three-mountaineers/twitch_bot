import requests
import logging
import json
import datetime
import tzlocal

from mountaineer_bot import windows_auth, twitch_auth
from mountaineer_bot.twitchauth import core

tz = tzlocal.get_localzone()

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
    
def get_user_live(cfg_dict, username: str):
    headers = {
        'Client-ID': cfg_dict['CLIENT_ID'],
        'Authorization': 'Bearer {}'.format(
            windows_auth.get_access_token(
                cfg_dict, 
                cfg_dict['CLIENT_ID']
                )
            ),
    }
    contents = requests.get(
        f'https://api.twitch.tv/helix/streams?user_login={username}',
        headers=headers,
    ).content
    contents_dict = json.loads(contents)
    if len(contents_dict['data']) > 0:
        return datetime.datetime.strptime(contents_dict['data'][0]['started_at'],'%Y-%m-%dT%H:%M:%SZ') + tz.utcoffset(datetime.datetime.now())
    else:
        return None