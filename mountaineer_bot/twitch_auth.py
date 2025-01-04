from typing import List
import os
import requests
from urllib import parse
import json
import configparser
import logging

import webbrowser
from flask import Flask, request as fsk_rqs, redirect, url_for

from mountaineer_bot import windows_auth

auth_url = 'https://id.twitch.tv/oauth2/authorize'
LOCAL_URL = 'http://localhost:{port}'

TWITCH_SCOPES = {
    'read_chat':'chat:read',
    'send_chat':'chat:edit',
    'read_whisper':'whispers:read',
    'send_whisper':'whispers:edit',
    'moderate_channel':'channel:moderate',
    'read_redemption':'channel:read:redemptions',
    'read_goals': 'channel:read:goals',
}

def get_scopes_file(config_path):
    config_dir = os.path.split(config_path)[0]
    return os.path.join(config_dir, 'granted_scopes.cfg')

def check_granted_scopes(config_path):
    scopes_path = get_scopes_file(config_path)
    scope_config = configparser.ConfigParser()
    configs = windows_auth.read_config(config_path, 'TWITCH_BOT')
    scope_config.read(scopes_path)
    if configs['CLIENT_ID'] in scope_config:
        config_all = {k:v for k,v in scope_config[configs['CLIENT_ID']].items()}
        granted = config_all.get('granted_scope','').split('\n')
        granted = [x for x in granted if x!='']
    else:
        granted = []
    return granted

def save_granted_scopes(config_path, scopes:List[str]):
    scopes = list(set(scopes))
    scopes_path = get_scopes_file(config_path)
    scope_config = configparser.ConfigParser()
    configs = windows_auth.read_config(config_path, 'TWITCH_BOT')
    scope_config.read(scopes_path)
    if configs['CLIENT_ID'] not in scope_config:
        scope_config.add_section(configs['CLIENT_ID'])
        granted = []
    else:
        config_all = {k.upper():v for k,v in scope_config[configs['CLIENT_ID']].items()}
        granted = config_all.get('granted_scope',[])
    scopes = '\n'.join(scopes + granted)
    scope_config.set(configs['CLIENT_ID'], 'granted_scope', scopes)
    with open(scopes_path, 'w') as f:
        scope_config.write(f)

def get_scopes(scopes:List[str]=[]):
    raw_scopes = [TWITCH_SCOPES[x] if x in TWITCH_SCOPES else x for x in scopes]
    raw_scopes = [x for x in raw_scopes if x in TWITCH_SCOPES.values()]
    return set(raw_scopes)

def parse_scopes_to_url(scopes):
    url_scopes = ' '.join(scopes)
    url_scopes = parse.quote(url_scopes)
    return url_scopes

def main(config, scopes=['read_chat']) -> Flask:
    configs = windows_auth.get_password(windows_auth.read_config(config, 'TWITCH_BOT'))
    app = Flask(__name__)
    granted_scopes = check_granted_scopes(config)
    scopes = get_scopes(scopes)
    new_scopes = [x for x in scopes if x not in granted_scopes]
    full_scope = new_scopes + granted_scopes

    redirect_uri = LOCAL_URL.format(port=configs['PORT'])

    @app.route('/')
    def home():
        args = fsk_rqs.args
        if 'code' not in args.keys():
            return "Success. Implicit token requested. Please check the URL for your token (I can't see this.)"
        else:
            return redirect(url_for('code_login_get_token', user=args['state'], code=args['code']))

    @app.route('/implicit_login/<user>')
    def implicit_login(user):
        uri = '{auth_url}?response_type=token&client_id={client_id}&redirect_uri={redirect_uri}&scope={scopes}&state={user}'
        return redirect(uri.format(auth_url=auth_url, client_id=configs['CLIENT_ID'], redirect_uri=redirect_uri, user=user, scopes=parse_scopes_to_url(full_scope)))

    @app.route('/login/<user>')
    def code_login(user):
        uri = '{auth_url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scopes}&state={user}'
        return redirect(uri.format(auth_url=auth_url, client_id=configs['CLIENT_ID'], redirect_uri=redirect_uri, user=user, scopes=parse_scopes_to_url(full_scope)))

    @app.route('/<user>/<code>')
    def code_login_get_token(user, code):
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
        }
        data = {
            'client_id': configs['CLIENT_ID'],
            'client_secret': configs['SECRET'],
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }
        r = requests.post('https://id.twitch.tv/oauth2/token', headers=headers, data=data)
        result = json.loads(r.content)
        windows_auth.set_refresh_token(configs, user, result['refresh_token'])
        save_granted_scopes(config_path=config, scopes=full_scope)
        return 'Successfully authorized using code flow. You can close this application now by hitting Ctrl + C in the command window.'
    
    if len(new_scopes) > 0:
        webbrowser.open(LOCAL_URL.format(port=configs['PORT'])+f'/login/{configs["BOT_NICK"]}')
        app.run(port=configs['PORT'], debug=False)
    else:
        logging.log(logging.INFO, 'All required clients scopes have been granted. Continuing.')
    return

def refresh_access_token(config_str):
    config = windows_auth.get_password(windows_auth.read_config(config_str, 'TWITCH_BOT'))
    refresh_token = windows_auth.get_refresh_token(config, config['CLIENT_ID'])
    redirect_uri = LOCAL_URL.format(port=config['PORT'])
    headers = {
        'Content-type': 'application/x-www-form-urlencoded',
    }
    data = {
        'client_id': config['CLIENT_ID'],
        'client_secret': config['SECRET'],
        'refresh_token': refresh_token,
        'redirect_uri': redirect_uri,
        'grant_type': 'refresh_token',
    }
    r = requests.post('https://id.twitch.tv/oauth2/token', headers=headers, data=data)
    result = json.loads(r.content)
    windows_auth.set_refresh_token(config, config['CLIENT_ID'], result['refresh_token'])
    return result['access_token']

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config', type=str)
    parser.add_argument('-s','--scopes', nargs='+', default=['chat:read'])
    args = vars(parser.parse_args())
    app = main(**args)