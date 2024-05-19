import os
from typing import List
import logging

from twitchio.ext import commands

from mountaineer_bot import windows_auth
from mountaineer_bot.twitchauth import core as twitch_auth_core

from typing import Literal, List
from functools import wraps

from mountaineer_bot import core

def restrict_command(
        allowed: List[Literal['Whitelist', 'Broadcaster', 'Mods']]=['Broadcaster'], 
        default=False, 
        blacklist_enabled=True
    ):
    def decorator(func):
        @wraps(func)
        async def wrapper(self: "Bot", ctx, *args, **kwargs):
            if 'Broadcaster' in allowed and ctx.author.is_broadcaster:
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
                if self._no_permission_response is not None:
                    await self.send(ctx, self._no_permission_response)
            else:
                await func(self, ctx, *args, **kwargs)
        return wrapper
    return decorator

class BotMixin:
    _required_scope: List[str] = []
    def __init__(self, config_file: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = windows_auth.get_password(windows_auth.read_config(config_file))
        self._config_dir = os.path.split(config_file)[0]
        self._repeat_preventer = '\U000e0000'

    async def send(self, ctx, message):
        if message is not None:
            await ctx.send(self.ck(message))
        return

    def parse_content(self, s):
        return s.strip(self._repeat_preventer).strip().replace(self._repeat_preventer, '').split()
    
    @classmethod
    def get_required_scope(cls):
        if hasattr(super(), 'get_required_scope'):
            parent_scope = super().get_required_scope()
        else:
            parent_scope = []
        return list(set(cls._required_scope + parent_scope))

class Bot(BotMixin, commands.Bot):
    _required_scope = [
        'chat:read',
    ]
    def __init__(
        self,
        config_file: str,
        **kwargs
    ):
        _configs = windows_auth.get_password(windows_auth.read_config(config_file))
        super().__init__(
            config_file=config_file,
            token=windows_auth.get_access_token(_configs, _configs['CLIENT_ID']),
            prefix= _configs['BOT_PREFIX'],
            client_id = _configs['CLIENT_ID'], 
            client_secret = _configs['SECRET'],
            initial_channels = _configs['CHANNELS'],
            nick = _configs['BOT_NICK'], 
            loop = None,
            heartbeat = 30,
            retain_cache = True,
            **kwargs
            )
        self._http._refresh_token = windows_auth.get_refresh_token(config=self._config, username=_configs['BOT_NICK'])
        self._user = _configs['BOT_NICK']
        self._invalid_response = self._config.get('INVALID_COMMAND_RESPONSE')
        self._no_permission_response = self._config.get('NO_PERMISSION_RESPONSE')
        self._bot_whitelist = self._config.get('WHITE_LIST_USERS',[])
        self._bot_blacklist = self._config.get('BLACK_LIST_USERS',[])
        self._repeat_preventer = '\U000e0000'
        self._last_message = '' 

    def run(self):
        logging.info('Running in channels: {}'.format(', '.join(self._config['CHANNELS'])))
        super().run()

    def ck(self, message):
        if self._last_message == message:
            self._last_message = message + self._repeat_preventer
            return message + self._repeat_preventer
        self._last_message = message
        return message

    async def event_ready(self):
        logging.info(f"{self.nick} is online!")

    @commands.command()
    async def where(self, ctx: commands.Context):
        logging.info("I've been hailed!")
        await self.send(ctx, f'Hello, I am here!')

    @commands.command()
    async def hello(self, ctx: commands.Context):
        logging.info("[hello] I've been hailed!")
        await self.send(ctx, f'Hello {ctx.author.name}!')

    @commands.command()
    @restrict_command(['Mods', 'Broadcaster'])
    async def add_whitelist(self, ctx: commands.Context):
        content = self.parse_content(ctx.message.content)
        if content[1] not in self._bot_whitelist:
            await self.send(ctx, f"You're cool {content[1]}")
            self._bot_whitelist.append(content[1])
        else:
            await self.send(ctx, f"{content[1]} is already cool with me!")

    @commands.command()
    @restrict_command(['Mods', 'Broadcaster'])
    async def remove_whitelist(self, ctx: commands.Context):
        content = self.parse_content(ctx.message.content)
        if content[1] not in self._bot_whitelist:
            await self.send(ctx, f"I wasn't cool with you anyway {content[1]}")
        else:
            await self.send(ctx, f"You're dead to me {content[1]}!")
            self._bot_whitelist.remove(content[1])

    @commands.command()
    @restrict_command(['Mods', 'Broadcaster'])
    async def add_blacklist(self, ctx: commands.Context):
        content = self.parse_content(ctx.message.content)
        if content[1] not in self._bot_blacklist:
            await self.send(ctx, f"You're dead to me {content[1]}")
            self._bot_blacklist.append(content[1])
        else:
            await self.send(ctx, f"{content[1]} is already dead to me.")

    @commands.command()
    @restrict_command(['Mods', 'Broadcaster'])
    async def remove_blacklist(self, ctx: commands.Context):
        content = self.parse_content(ctx.message.content)
        if content[1] not in self._bot_blacklist:
            await self.send(ctx, f"I was cool with you already {content[1]} :)")
        else:
            await self.send(ctx, f"You're cool again I guess {content[1]}!")
            self._bot_blacklist.remove(content[1])

    @commands.command()
    @restrict_command(['Mods', 'Broadcaster'])
    async def blacklist(self, ctx: commands.Context):
        blaclist = ', '.join(self._bot_blacklist)
        await self.send(ctx, f"Naughty Chatters:  {blaclist}")

    @commands.command()
    @restrict_command(['Mods', 'Broadcaster'])
    async def whitelist(self, ctx: commands.Context):
        whitelist = ', '.join(self._bot_whitelist)
        await self.send(ctx, f"Very nice chatters:  {whitelist}")