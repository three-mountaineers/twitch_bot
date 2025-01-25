import time
from typing import Type
import traceback
import logging
import appdirs
import os
import asyncio

from mountaineer_bot import core

async def main(Bot: Type[core.Bot], profile: str, event_profile: None | str=None, headless: bool=False, dryrun: bool = False, live_only:bool = False, respond: bool=False):
    bot = Bot(profile=profile, event_profile=event_profile, dryrun=dryrun, headless=headless, live_only=live_only, respond=respond)
    await bot.start()

def main_instantiator(Bot:  Type[core.Bot]):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--profile', type=str)
    parser.add_argument('-e','--event_profile', type=str, default=None)
    parser.add_argument('-d','--headless', action='store_true')
    parser.add_argument('-l','--live_only', action='store_true')
    parser.add_argument('-r','--respond', action='store_true')
    parser.add_argument('--dryrun', action='store_true')
    parser.add_argument('--log_level', default=20, type=int)
    args = vars(parser.parse_args())
    log_level = args.pop('log_level')
    logging.getLogger().setLevel(log_level)
    while 1:
        try:
            asyncio.run(main(Bot=Bot, **args))
        except KeyError as e:
            logging.log(logging.FATAL, 'Error encountered')
            logging.log(logging.FATAL, traceback.format_exc())
            logging.log(logging.FATAL, 'Rebooting...')
            time.sleep(60)

if __name__ == "__main__":
    main_instantiator(core.Bot)