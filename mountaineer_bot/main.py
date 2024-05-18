from mountaineer_bot import windows_auth, core, twitch_auth
from mountaineer_bot.twitchauth import device_flow, core as twitch_auth_core
import time
from typing import Type
import traceback

def main(Bot: Type[core.Bot], config: str, headless: bool=False):
    granted_scopes = twitch_auth_core.refresh_token(config)
    if granted_scopes is None:
        missing_scopes = Bot.get_required_scope()
        granted_scopes = []
    else:
        missing_scopes = [x for x in Bot.get_required_scope() if x not in granted_scopes]
    if len(missing_scopes):
        print(f'Missing scopes: {missing_scopes}')
        device_flow.initial_authenticate(config_str=config, scopes=granted_scopes+missing_scopes, headless=headless)
    bot = Bot(config_file=config)
    bot.run()

def main_instantiator(Bot:  Type[core.Bot]):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config', type=str)
    parser.add_argument('-d','--headless', action='store_true')
    args = vars(parser.parse_args())
    while 1:
        try:
            main(Bot=Bot, **args)
        except KeyError as e:
            print('Error encountered')
            print(traceback.format_exc())
            print('Rebooting...')
            time.sleep(60)

if __name__ == "__main__":
    main_instantiator(core.Bot)