import configparser
import keyring

def read_config(cfg_location):
    config = configparser.ConfigParser()
    config.read(cfg_location)
    config = {k.upper():v for k,v in config['TWITCH_BOT'].items()}
    config['CHANNELS'] = config['CHANNELS'].split()
    if 'WHITE_LIST_USERS' in config.keys():
        config['WHITE_LIST_USERS'] = config['WHITE_LIST_USERS'].split()
    return config

def get_password(config):
    config['SECRET'] = keyring.get_password(config['WIN_CRED_KEY'], config['CLIENT_ID'])
    return config

def set_refresh_token(config, username, refresh_token):
    keyring.set_password(service_name=config['WIN_CRED_KEY'], username=username+'_refresh_token', password=refresh_token)

def get_refresh_token(config, username):
    return keyring.get_password(service_name=config['WIN_CRED_KEY'], username=username+'_refresh_token')