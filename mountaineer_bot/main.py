import time
from typing import Type
import traceback
import logging
import appdirs
import os

from mountaineer_bot import windows_auth, core, twitch_auth, _cfg_loc
from mountaineer_bot.twitchauth import device_flow, core as twitch_auth_core

def main(Bot: Type[core.Bot], profile: str, headless: bool=False):
    appdir = appdirs.AppDirs(
        appname=profile,
        appauthor=_cfg_loc,
        roaming=True,
    )
    config = os.path.join(appdir.user_config_dir, 'env.cfg')
    granted_scopes = twitch_auth_core.refresh_token(config)
    logging.info(f'Granted scopes: {", ".join(granted_scopes)}')
    if granted_scopes is None:
        missing_scopes = Bot.get_required_scope()
        granted_scopes = []
    else:
        missing_scopes = [x for x in Bot.get_required_scope() if x not in granted_scopes]
    logging.info(f'Missing scopes: {", ".join(missing_scopes)}')
    if len(missing_scopes):
        logging.log(logging.INFO, f'Missing scopes: {missing_scopes}')
        device_flow.initial_authenticate(config_str=config, scopes=granted_scopes+missing_scopes, headless=headless)
    bot = Bot(config_file=config)
    bot.run()

def main_instantiator(Bot:  Type[core.Bot]):
    logging.getLogger().setLevel(logging.INFO)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--profile', type=str)
    parser.add_argument('-d','--headless', action='store_true')
    args = vars(parser.parse_args())
    while 1:
        try:
            main(Bot=Bot, **args)
        except KeyError as e:
            logging.log(logging.FATAL, 'Error encountered')
            logging.log(logging.FATAL, traceback.format_exc())
            logging.log(logging.FATAL, 'Rebooting...')
            time.sleep(60)

if __name__ == "__main__":
    main_instantiator(core.Bot)