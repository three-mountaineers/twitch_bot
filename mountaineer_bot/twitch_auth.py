from typing import List

import requests
from urllib import parse
from flask import Flask, request as fsk_rqs, redirect, url_for
import json

from mountaineer_bot import windows_auth

auth_url = 'https://id.twitch.tv/oauth2/authorize'

TWITCH_SCOPES = {
    'read_chat':'chat:read',
    'send_chat':'chat:edit',
    'read_whisper':'whispers:read',
    'send_whisper':'whispers:edit',
    'moderate_channel':'channel:moderate',
}

def get_scopes(scopes:List[str]=[], raw_scopes:List[str]=[]):
    scopes = ' '.join([TWITCH_SCOPES[x] for x in scopes]+raw_scopes)
    scopes = parse.quote(scopes)
    return scopes

def main(config) -> Flask:
    configs = windows_auth.get_password(windows_auth.read_config(config))
    app = Flask(__name__)

    redirect_uri = 'http://localhost:{port}'.format(port=configs['PORT'])

    @app.route('/')
    def home():
        args = fsk_rqs.args
        if 'code' not in args.keys():
            return "Success. Implicit token requested. Please check the URL for your token (I can't see this.)"
        else:
            return redirect(url_for('code_login_get_token', user=args['state'], code=args['code']))

    @app.route('/implicit_login/<user>')
    def implicit_login(user):
        scopes = get_scopes(scopes=['read_chat','send_chat'])
        uri = '{auth_url}?response_type=token&client_id={client_id}&redirect_uri={redirect_uri}&scope={scopes}&state={user}'
        return redirect(uri.format(auth_url=auth_url, client_id=configs['CLIENT_ID'], redirect_uri=redirect_uri, user=user, scopes=scopes))

    @app.route('/login/<user>')
    def code_login(user):
        scopes = get_scopes(scopes=['read_chat','send_chat'])
        uri = '{auth_url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scopes}&state={user}'
        return redirect(uri.format(auth_url=auth_url, client_id=configs['CLIENT_ID'], redirect_uri=redirect_uri, user=user, scopes=scopes))

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
        return 'Successfully authorized using code flow.'
    
    app.run(port=configs['PORT'], debug=True)       

def refresh_access_token(config, user):
    refresh_token = windows_auth.get_refresh_token(config, user)
    redirect_uri = 'http://localhost:{port}'.format(port=config['PORT'])
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
    windows_auth.set_refresh_token(config, user, result['refresh_token'])
    return result['access_token']

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config', type=str)
    args = vars(parser.parse_args())
    app = main(**args)