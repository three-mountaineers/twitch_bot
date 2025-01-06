from mountaineer_bot.core import BotMixin, BotEventMixin, BotEventListener, Bot

import os

_module_path_ = os.path.split(os.path.abspath(__file__))[0]
_cfg_loc = 'mountaineer_twitchbot_app'

del os