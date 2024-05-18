from typing import List
import requests
import json
from urllib import parse
import time
import webbrowser
import logging

from mountaineer_bot import windows_auth

def parse_scopes_to_url(scopes):
    url_scopes = ' '.join(scopes)
    return url_scopes

def initial_authenticate(config_str, scopes: List[str], headless: bool=False):
    config = windows_auth.get_password(windows_auth.read_config(config_str))
    headers = {
        'Content-type': 'application/x-www-form-urlencoded',
    }
    data = {
        'client_id': config['CLIENT_ID'],
        'scopes': parse_scopes_to_url(scopes),
    }
    r = requests.post('https://id.twitch.tv/oauth2/device', headers=headers, data=data)
    main_result = json.loads(r.content)
    if headless:
        logging.log(100, f'Please open this link in your browser: {main_result["verification_uri"]}')
    else:
        webbrowser.open(main_result["verification_uri"])
    logging.log(100, f'The activation code is: {main_result["user_code"]}')

    t = time.time()
    grant = False
    while (time.time() - t < main_result['expires_in']) and not grant:
        data = {
            'client_id': config['CLIENT_ID'],
            'scopes': parse_scopes_to_url(scopes),
            'device_code': main_result['device_code'],
            'grant_type': "urn:ietf:params:oauth:grant-type:device_code",
        }
        r = requests.post('https://id.twitch.tv/oauth2/token', headers=headers, data=data)
        result = json.loads(r.content)
        grant = result.get('status', 200) == 200
        
        if not grant:
            time.sleep(main_result['interval']+1)

    if not grant:
        raise RuntimeError('Device code has expired. Please restart the application.')

    windows_auth.set_refresh_token(config, config['CLIENT_ID'], result['refresh_token'])
    windows_auth.set_access_token(config, config['CLIENT_ID'], result['access_token'])