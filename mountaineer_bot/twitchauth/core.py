import requests
import json

from mountaineer_bot import windows_auth

def refresh_token(config_str):
    config = windows_auth.get_password(windows_auth.read_config(config_str))
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
    windows_auth.set_refresh_token(config, config['CLIENT_ID'], result['refresh_token'])
    windows_auth.set_access_token(config, config['CLIENT_ID'], result['access_token'])
    return result['scope']