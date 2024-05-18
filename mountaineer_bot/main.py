from mountaineer_bot import windows_auth, core, twitch_auth
import time
from typing import Type
import traceback

def main(bot: Type[core.Bot], config):
    try:
        bot = bot(config_file=config)
    except KeyError:
        twitch_auth.main(config)
        bot = bot(config_file=config)
    granted_scopes = twitch_auth.check_granted_scopes(config)
    missing_scopes = [x for x in bot._required_scope if x not in granted_scopes]
    if len(missing_scopes):
        twitch_auth.main(config, scopes=missing_scopes)
    else:
        bot.run()

def main_instantiator(bot:  Type[core.Bot]):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config', type=str)
    args = vars(parser.parse_args())
    while 1:
        try:
            main(bot=bot, **args)
        except KeyError as e:
            print('Error encountered')
            print(traceback.format_exc())
            print('Rebooting...')
            time.sleep(60)

if __name__ == "__main__":
    main_instantiator(core.Bot)