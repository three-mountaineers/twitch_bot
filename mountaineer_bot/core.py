import os
from typing import List, Optional, Literal, TypedDict, TYPE_CHECKING, Protocol
import logging
import time
import requests
import json
import datetime
import tzlocal
import pytz
import asyncio
from functools import wraps
import appdirs

from twitchio.ext import commands

#from mountaineer_bot.mixins import BotEventMixin, BotMixin
from mountaineer_bot.tw_events.core import TwitchWebSocket
from mountaineer_bot.tw_events import scopes
from mountaineer_bot import windows_auth, utils
from mountaineer_bot.twitch_auth import core as twitch_auth_core, device_flow
import mountaineer_bot as mtb

from mountaineer_bot import api
from mountaineer_bot.security import restrict_command

class MessageItem(TypedDict):
    message: str
    priority: int
    order: utils.NotRequired[int]

def to_list(val: str | list[str]):
    if isinstance(val, str):
        return [val]
    else:
        return val

class TwitchBotConfig(TypedDict):
    CLIENT_ID: str
    SECRET: utils.NotRequired[str]
    BOT_PREFIX: str
    CHANNELS: list[str]
    BOT_NICK: str
    INVALID_COMMAND_RESPONSE: str
    NO_PERMISSION_RESPONSE: str
    WHITE_LIST_USERS: list[str]
    BLACK_LIST_USERS: list[str]

class Bot(commands.Bot):
    def __init__(
        self,
        profile: str,
        dryrun: bool = True,
        headless: bool = False,
        live_only: bool = False,
        **kwargs
    ):
        self._appdir = appdirs.AppDirs(
            appname=profile,
            appauthor=mtb._cfg_loc,
            roaming=True,
        )
        self._config_file = os.path.join(self._appdir.user_config_dir, 'env.cfg')
        self.live_only = live_only
        self._config = windows_auth.read_config(self._config_file, key=None)
        configs: TwitchBotConfig = self._config['TWITCH_BOT']
        windows_auth.get_password(self._config['TWITCH_BOT'])
        self.add_required_scope([
            'chat:read',
        ])
        self.login(headless=headless)
        super().__init__(
            config_file=self._config_file,
            token=windows_auth.get_access_token(configs, configs['CLIENT_ID']),
            prefix= configs['BOT_PREFIX'],
            client_id = configs['CLIENT_ID'], 
            client_secret = configs['SECRET'],
            initial_channels = to_list(configs['CHANNELS']),
            nick = configs['BOT_NICK'], 
            loop = None,
            heartbeat = 30,
            retain_cache = True,
            **kwargs
            )
        self._http._refresh_token = windows_auth.get_refresh_token(config=configs, username=configs['BOT_NICK'])
        self._user = configs['BOT_NICK']
        self._invalid_response = configs.get('INVALID_COMMAND_RESPONSE', '')
        self._no_permission_response = configs.get('NO_PERMISSION_RESPONSE', '')
        self._channels = to_list(configs.get('CHANNELS', []))
        self._bot_whitelist = to_list(configs.get('WHITE_LIST_USERS', []))
        self._bot_blacklist = to_list(configs.get('BLACK_LIST_USERS', []))
        self._repeat_preventer = '\U000e0000'
        self._last_message = '' 
        self._is_live: dict[str, datetime.datetime | None] = {}
        self._dryrun = dryrun
        self._message_queue: list[MessageItem] = []
        self._message_queue_routine: None | asyncio.Task = None
        self._message_idx = 0

    def save_config(self):
        windows_auth.write_config(self._config_file, self._config)

    async def _send(self, ctx: commands.Context):
        while len(self._message_queue) > 0:
            self._message_queue = list(sorted(self._message_queue, key=lambda x: (x['priority'], x['order'])))
            message = self._message_queue.pop(0)
            if self._dryrun:
                logging.info(f"[{len(self._message_queue)}]: {self.ck(message['message'])}")
            else:
                await ctx.send(self.ck(message['message']))
            await asyncio.sleep(0.5)
    
    async def send(self, ctx: commands.Context, message: Optional[str], priority: int=1):
        if message is None:
            return
        self._message_idx += 1
        self._message_queue.append({
            'message': message,
            'priority': priority,
            'order': self._message_idx,
        })
        
        if self._message_queue_routine is None:
            self._message_queue_routine = asyncio.create_task(self._send(ctx=ctx))
        elif self._message_queue_routine.done():
            self._message_queue_routine = asyncio.create_task(self._send(ctx=ctx))

    def parse_content(self, s: str):
        return s.strip(self._repeat_preventer).strip().replace(self._repeat_preventer, '').split()

    def login(self, headless: bool=False):
        logging.info(f"Logging into account: {self._config['TWITCH_BOT']['BOT_NICK']}")
        granted_scopes = twitch_auth_core.get_scope(self._config['TWITCH_BOT'])
        if granted_scopes is None:
            logging.info(f'Granted scopes: None')
            missing_scopes = self.required_scope
            granted_scopes = []
        else:
            logging.info(f'Granted scopes: {", ".join(granted_scopes)}')
            missing_scopes = [x for x in self.required_scope if x not in granted_scopes]
        logging.info(f'Missing scopes: {", ".join(missing_scopes)}')
        if len(missing_scopes):
            logging.info(f'Missing scopes: {missing_scopes}')
            device_flow.initial_authenticate(config=self._config['TWITCH_BOT'], scopes=granted_scopes+missing_scopes, headless=headless)

    @property
    def required_scope(self):
        if not hasattr(self, '_required_scope'):
            return []
        else:
            return self._required_scope

    def add_required_scope(self, scopes: list[str]):
        self._required_scope = list(set(self.required_scope + scopes))

    async def start(self):
        logging.info('Running bot in channels: {}'.format(', '.join(self._channels)))
        await super().start()

    def run(self):
        logging.info('Running bot in channels: {}'.format(', '.join(self._channels)))
        super().run()

    def is_live(self, channel):
        return self._is_live.get(channel) is not None

    def ck(self, message: str):
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
        await self.send(ctx, f'Hello, I am here!', priority=0)

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

class BotEventListener(Bot):
    def __init__(
            self,
            event_profile: str,
            *args,
            **kwargs,
    ):
        self.tws = TwitchWebSocket(profile=event_profile, bot=self)
        super().__init__(*args, **kwargs)
        
    async def start(self):
        logging.info(f"Running listener with account {self.tws.config['TWITCH_BOT']['BOT_NICK']}")
        if self.tws is not None:
            asyncio.create_task(self.tws.start())
        await super().start()
    
    def run(self):
        logging.info(f"Running listener with account {self.tws.config['TWITCH_BOT']['BOT_NICK']}")
        if self.tws is not None:
            asyncio.create_task(self.tws.start())
        super().run()

class BotMixin(Bot):
    pass

class BotEventMixin(BotEventListener):
    tws: "TwitchWebSocket"
    pass

def pass_message(cls,  message_dict):
    pass

for scope in scopes.REQUIRED_SCOPE.keys():
    setattr(BotEventMixin, scope.replace('.','_'), pass_message)

