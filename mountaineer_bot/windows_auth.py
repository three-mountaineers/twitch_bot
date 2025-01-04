import configparser
from typing import Optional, overload, Any
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

def split_delimit_string(text: str) -> str | list[str]:
    output = [x for x in text.split('\n') if x!= '']
    if len(output) > 1:
        return output
    else:
        return output[0]

@overload
def read_config(cfg_location: str, key: None = None) -> dict[str, dict[str, Any]]:
    ...

@overload
def read_config(cfg_location: str, key: str) -> dict[str, Any]:
    ...

def read_config(cfg_location: str, key: Optional[str] = None):
    config = configparser.ConfigParser()
    config.read(cfg_location)
    if key is None:
        output = {k.upper(): {kk.upper(): split_delimit_string(vv) for kk, vv in v.items() if vv != ''} for k,v in config.items()}
    elif key in config:
        output = {k.upper(): split_delimit_string(v) for k,v in config[key].items() if v != ''}
    else:
        output = {}
    return output

def write_config(cfg_location: str, val: dict, key: Optional[str]=None):
    config = configparser.ConfigParser()
    if key is not None:
        config.read(cfg_location)
        config[key] = val
    else:
        for k,v in val.items():
            if k != 'DEFAULT':
                config.add_section(k)
            for kk, vv in v.items():
                if kk == 'SECRET':
                    pass
                elif isinstance(vv, list):
                    config[k][kk] = '\n' + '\n'.join([''] + vv)
                else:
                    config[k][kk] = vv
    with open(cfg_location, 'w') as f:
        config.write(f)

def set_password(config, secret):
    keyring.set_password(config['WIN_CRED_KEY'], config['CLIENT_ID'], password=secret)

def get_password(config):
    config['SECRET'] = keyring.get_password(config['WIN_CRED_KEY'], config['CLIENT_ID'])
    return config

def set_refresh_token(config, username, refresh_token):
    keyring.set_password(service_name=config['WIN_CRED_KEY'], username=username+'_refresh_token', password=refresh_token)

def get_refresh_token(config, username):
    try:
        output = keyring.get_password(service_name=config['WIN_CRED_KEY'], username=username+'_refresh_token')
    except KeyError:
        output =  None
    return output

def set_access_token(config, username, refresh_token):
    keyring.set_password(service_name=config['WIN_CRED_KEY'], username=username+'_access_token', password=refresh_token)

def get_access_token(config, username):
    try:
        output = keyring.get_password(service_name=config['WIN_CRED_KEY'], username=username+'_access_token')
    except KeyError:
        output =  None
    return output

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=str)
    parser.add_argument('secret', type=str)
    args = vars(parser.parse_args())
    configs = read_config(args['config'])
    set_password(configs, args['secret'])
