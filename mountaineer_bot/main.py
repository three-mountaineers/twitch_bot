import time
from typing import Type
import traceback
import logging
import appdirs
import os
import asyncio

from mountaineer_bot import windows_auth, core, twitch_auth
import mountaineer_bot as mtb
from mountaineer_bot.twitchauth import device_flow, core as twitch_auth_core
from mountaineer_bot.tw_events.core import TwitchWebSocket, BotEventMixin

async def main(Bot: Type[core.Bot], profile: str, EventBot: None | Type[TwitchWebSocket]=None, event_profile: None | str=None, headless: bool=False, dryrun: bool = False):
    bot = Bot(profile=profile, dryrun=dryrun)
    if EventBot is not None:
        if event_profile is None:
            raise ValueError('If EventBot is passed, event_profile must also be passed. This profile should be the broadcaster itself.')
        if not isinstance(bot, BotEventMixin):
            raise ValueError('Bot is not of subclass BotEventMixin. Bot must inherit from BotEventMixin for correct functioning with event listener.')
        ws = EventBot(profile=event_profile, bot=bot)
        asyncio.create_task(ws.start())
    else:
        if isinstance(bot, BotEventMixin):
            raise ValueError('Bot is of subclass BotEventMixin. If Bot inherits from BotEventMixin, then an event listener profile (for the channel you\'re listening to) must be provided.')
        ws = None
    await bot.start()

def main_instantiator(Bot:  Type[core.Bot], EventBot: None | Type[TwitchWebSocket]=None):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--profile', type=str)
    parser.add_argument('-e','--event_profile', type=str, default=None)
    parser.add_argument('-d','--headless', action='store_true')
    parser.add_argument('--dryrun', action='store_true')
    args = vars(parser.parse_args())
    if args['dryrun']:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    while 1:
        try:
            asyncio.run(main(Bot=Bot, EventBot=EventBot, **args))
        except KeyError as e:
            logging.log(logging.FATAL, 'Error encountered')
            logging.log(logging.FATAL, traceback.format_exc())
            logging.log(logging.FATAL, 'Rebooting...')
            time.sleep(60)

if __name__ == "__main__":
    main_instantiator(core.Bot, None)