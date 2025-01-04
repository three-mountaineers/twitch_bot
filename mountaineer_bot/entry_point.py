from typing import Type
import os

from mountaineer_bot import windows_auth, twitch_auth
from mountaineer_bot.core import Bot
from mountaineer_bot.twitch_auth import main as grant_scope_main

def main(BotClass: Type[Bot]):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config_file', type=str)
    args = vars(parser.parse_args())
    configs = windows_auth.get_password(windows_auth.read_config(args['config_file'], 'TWITCH_BOT'))
    bot = BotClass(**args)
    scopes = bot._required_scope
    grant_scope_main(config=args['config_file'], scopes=scopes)
    if 'refresh_token' not in configs:
        bot = BotClass(**args)
    bot.run()