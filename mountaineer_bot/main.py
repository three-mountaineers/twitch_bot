from mountaineer_bot import windows_auth, core
import time
from typing import Type

def main(bot: Type[core.Bot], config, user):
    bot = bot(config_file=config, user=user)
    bot.run()

def main_instantiator(bot:  Type[core.Bot]):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config', type=str)
    parser.add_argument('-u','--user', type=str)
    args = vars(parser.parse_args())
    while 1:
        try:
            main(bot=bot, **args)
        except KeyError as e:
            print('Error encountered')
            breakpoint()
            print('Rebooting...')
            time.sleep(60)

if __name__ == "__main__":
    main_instantiator(core.Bot)