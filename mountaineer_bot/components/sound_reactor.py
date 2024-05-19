from typing import Optional, Dict
import logging

from twitchio.ext import commands, routines
from twitchio.message import Message

from mountaineer_bot import BotMixin
from mountaineer_bot.security import restrict_command

class SoundReactor(BotMixin):
    _required_scope = [
        'chat:read',
    ]

    async def event_message(self, message: Message):
        await super().event_message(message=message)
        if message.author is None:
            return
        logging.info(f'[{message.channel.name}] {message.author.name}: {message.content}')