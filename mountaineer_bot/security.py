from typing import Literal, List
from functools import wraps
from twitchio.ext import commands
from twitchio.message import Message

from mountaineer_bot import core, api

import logging

def restrict_message(
        allowed: List[Literal['Whitelist', 'Broadcaster', 'Mods']]=['Broadcaster'], 
        default: bool = False, 
        blacklist_enabled: bool = True,
        live_only: bool = False,
        fail_no_message: bool = False,
    ):
    def decorator(func):
        @wraps(func)
        async def wrapper(self: "core.Bot", message: Message, *args, **kwargs):
            channel_is_live = self.is_live(message.channel.name)
            if live_only and not channel_is_live:
                return
            elif message.author is None:
                return
            elif 'Broadcaster' in allowed and message.author.is_broadcaster:
                is_allowed = True
            elif blacklist_enabled and message.author.name in self._bot_blacklist:
                is_allowed = False
            elif 'Mods' in allowed and message.author.is_mod:
                is_allowed = True
            elif 'Whitelist' in allowed and message.author.name in self._bot_whitelist:
                is_allowed = True
            else:
                is_allowed = default
            if not is_allowed:
                if self._no_permission_response is not None and not fail_no_message:
                    await message.channel.send(self._no_permission_response)
            else:
                await func(self, message, *args, **kwargs)
        return wrapper
    return decorator

def restrict_command(
        allowed: List[Literal['Whitelist', 'Broadcaster', 'Mods']]=['Broadcaster'], 
        default: bool = False, 
        blacklist_enabled: bool = True,
        live_only: bool = False,
        fail_no_message: bool = False,
    ):
    def decorator(func):
        @wraps(func)
        async def wrapper(self: "core.Bot", ctx: commands.Context, *args, **kwargs):
            channel_is_live = self.is_live(ctx.channel.name)
            print(channel_is_live)
            if live_only and not channel_is_live:
                return
            elif 'Broadcaster' in allowed and ctx.author.is_broadcaster:
                is_allowed = True
            elif blacklist_enabled and ctx.author.name in self._bot_blacklist:
                is_allowed = False
            elif 'Mods' in allowed and ctx.author.is_mod:
                is_allowed = True
            elif 'Whitelist' in allowed and ctx.author.name in self._bot_whitelist:
                is_allowed = True
            else:
                is_allowed = default
            if not is_allowed:
                if self._no_permission_response is not None and not fail_no_message:
                    await self.send(ctx, self._no_permission_response)
            else:
                await func(self, ctx, *args, **kwargs)
        return wrapper
    return decorator