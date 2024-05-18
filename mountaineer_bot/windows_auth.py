import configparser
from typing import Optional
import platform
import os
if platform.system() == 'Windows':
    import keyring
elif platform.system() == 'Linux':
    import stat
    class Keyring:
        def __init__(self):
            self._file_path = os.path.join(os.path.expanduser('~'), '.config/twitch_bot.cfg')
            if not os.path.isdir(os.path.split(self._file_path)[0]):
                os.makedirs(os.path.split(self._file_path)[0])
            if not os.path.isfile(self._file_path):
                with open(self._file_path, 'w') as f:
                    f.write('')
            os.chmod(self._file_path, ((stat.S_IWUSR & (~stat.S_IRGRP) & (~stat.S_IROTH)) | stat.S_IRUSR))
        def get_password(self, service_name: str, username: str) -> Optional[str]:
            cfg = configparser.ConfigParser()
            cfg.read(self._file_path)
            return cfg[service_name][username]

        def set_password(self, service_name: str, username: str, password: str):
            cfg = configparser.ConfigParser()
            cfg.read(self._file_path)
            if service_name not in cfg:
                cfg.add_section(service_name)
            cfg.set(service_name, username, password)
            with open(self._file_path, 'w') as f:
                cfg.write(f)
    keyring = Keyring()

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