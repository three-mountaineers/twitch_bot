import requests
import logging
import json
import datetime
import tzlocal
import warnings

from mountaineer_bot import windows_auth
from mountaineer_bot.twitch_auth import core, device_flow

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
    
def get_redeem_list(cfg_dict, username: str):
    granted_scopes = core.get_scope(cfg_dict)
    if 'channel:read:redemptions' not in granted_scopes:
        device_flow.initial_authenticate(
            cfg_dict, 
            scopes=granted_scopes + ['channel:read:redemptions'],
        )
    user_id = get_user_id(cfg_dict=cfg_dict, username=username)
    headers = {
        'Client-ID': cfg_dict['CLIENT_ID'],
        'Authorization': 'Bearer {}'.format(
            windows_auth.get_access_token(
                cfg_dict, 
                cfg_dict['CLIENT_ID']
                )
            ),
    }
    r = requests.get(
        f'https://api.twitch.tv/helix/channel_points/custom_rewards?broadcaster_id={user_id}',
        headers=headers,
    )
    contents_dict = json.loads(r.content)
    if r.status_code > 200 and r.status_code < 300:
        output = {
            x['id']: x['title']
            for x in contents_dict['data']
        }
    elif 'The broadcaster must have partner or affiliate status.' == contents_dict['message']:
        print('WARNING: No redemptions available. ' + contents_dict['message'])
        return {}
    else:
        raise RuntimeError(f'Get_redeem_list API call failed: {r.content}')
    return output