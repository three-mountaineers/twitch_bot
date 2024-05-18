from typing import Dict, Union, List
import os
import json
import re
import datetime
from random import randrange

from twitchio.ext import commands
from twitchio.message import Message

from mountaineer_bot import BotMixin
from mountaineer_bot.security import restrict_command

class FirstIdentifier(BotMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._redemption_file = os.path.join(self._config_dir, 'redemption_history.json')
        self._required_scope += ['chat:read', 'chat:edit', 'channel:read:redemptions']
        if not os.path.isfile(self._redemption_file):
            with open(self._redemption_file,'w') as f:
                json.dump(
                    {
                        x:[]
                        for x in self._config['CHANNELS']
                    },
                    f
                )
        with open(self._redemption_file,'r') as f:
            self._schedule: Dict[str, List[List]] = json.load(f)

    #def event(self, *args, **kwargs):
    #    pass
    #
    #@event
    async def event_message(self, message: Message):
        await super().event_message(message=message)
        #message.channel.send()
        print(f'[{message.channel.name}] {message.author.name}: {message.content}')
        pass