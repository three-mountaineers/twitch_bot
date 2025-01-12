import requests
import json
import logging

from mountaineer_bot import windows_auth

TWITCH_SCOPES = {
    'read_chat':'chat:read',
    'send_chat':'chat:edit',
    'read_whisper':'whispers:read',
    'send_whisper':'whispers:edit',
    'moderate_channel':'channel:moderate',
    'read_redemption':'channel:read:redemptions',
    'read_goals': 'channel:read:goals',
}

def get_scope(config):
    refresh_token = windows_auth.get_refresh_token(config, config['CLIENT_ID'])
    if refresh_token is None:
        return None
    access_token = windows_auth.get_access_token(config, config['CLIENT_ID'])
    headers = {
        'Content-type': 'application/x-www-form-urlencoded',
    }
    data = {
        'client_id': config['CLIENT_ID'],
        'client_secret': config['SECRET'],
        'access_token': access_token,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
    }
    r = requests.post('https://id.twitch.tv/oauth2/token', headers=headers, data=data)
    result = json.loads(r.content)
    if r.status_code != 200:
        logging.log(logging.FATAL, r.content)
        raise RuntimeError('Could not refresh token.')
    windows_auth.set_refresh_token(config, config['CLIENT_ID'], result['refresh_token'])
    windows_auth.set_access_token(config, config['CLIENT_ID'], result['access_token'])
    return result['scope']

def refresh_token(config):
    get_scope(config)