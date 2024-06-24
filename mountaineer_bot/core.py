import os
from typing import List
import logging
import time
import requests
import json
import datetime
import tzlocal
import pytz

from twitchio.ext import commands

from mountaineer_bot import windows_auth
from mountaineer_bot.twitchauth import core as twitch_auth_core

from typing import Literal, List
from functools import wraps

from mountaineer_bot import api
from mountaineer_bot.security import restrict_command

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
        self._live_status = {}

    def run(self):
        logging.info('Running in channels: {}'.format(', '.join(self._config['CHANNELS'])))
        super().run()

    def is_live(self, channel):
        t = time.time()
        if channel not in self._live_status or (t - self._live_status[channel]['time']) > 60:
            self._live_status[channel] = {
                'live': api.check_channel_is_live(channel),
                'time': t
            }
        return self._live_status[channel]['live']

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

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        headers = {
            'Client-ID': self._config['CLIENT_ID'],
            'Authorization': 'Bearer {}'.format(
                windows_auth.get_access_token(
                    self._config, 
                    self._config['CLIENT_ID']
                    )
                ),
        }
        contents = requests.get(
            f'https://api.twitch.tv/helix/streams?user_login={ctx.channel.name}',
            headers=headers,
        ).content
        contents_dict = json.loads(contents)
        if len(contents_dict['data']) > 0:
            now = datetime.datetime.now(tzlocal.get_localzone()).astimezone(pytz.utc).replace(tzinfo=None, microsecond=0)
            start_at_str = contents_dict['data'][0]['started_at']
            start_at = datetime.datetime.strptime(start_at_str,'%Y-%m-%dT%H:%M:%SZ')
            live_time = now - start_at
            await self.send(ctx, f"{ctx.channel.name} has been live for {live_time}")
        else:
            await self.send(ctx, f"{ctx.channel.name} is not live")