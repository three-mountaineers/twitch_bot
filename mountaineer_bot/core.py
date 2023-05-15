from typing import Union, Callable, Optional, Dict, List

import time
import asyncio
import math
import re
import json
import datetime
import os
from random import randrange

from twitchio.ext import commands, routines

from mountaineer_bot import windows_auth, twitch_auth

def allow_whitelist(self, ctx: commands.Context, allowed=False):
    if ctx.author.name in self._bot_whitelist:
        allowed = True
    return allowed

def allow_broadcaster(self, ctx: commands.Context, allowed=False):
    if ctx.author.is_broadcaster:
        allowed = True
    return allowed

def allow_mods(self, ctx: commands.Context, allowed=False):
    if ctx.author.is_mod:
        allowed = True
    return allowed

def to_float(s):
    try:
        return float(s)
    except:
        return None

class CountdownMixin:
    def __init__(self, countdown_go_text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cd: Dict[str, Dict[str, Optional[routines.Routine]]] = {channel:{} for channel in kwargs['initial_channels']}
        self._countdown_go_text = countdown_go_text
    
    @commands.command()
    async def cd(self, ctx: commands.Context):
        allowed = False
        allowed = allow_broadcaster(self, ctx, allowed)
        allowed = allow_mods(self, ctx, allowed)
        allowed = allow_whitelist(self, ctx, allowed)
        if not allowed:
            await ctx.send(self.ck(self._no_permission_response))
            return
        content = ctx.message.content.strip(self._repeat_preventer).strip().split(' ')
        channel = ctx.channel.name
        dt = to_float(content[1])
        
        if dt is None:
            if len(content) == 2:
                key = None
            else:
                key = content[2]
            if content[1].lower() in ['stop','wait']:
                message = self.stop_countdown(channel, key=key)
                await ctx.send(self.ck(message))
            else:
                if self._invalid_response is not None:
                    await ctx.send(self.ck(self._invalid_response))
        elif dt <= 0:
            if self._invalid_response is not None:
                await ctx.send(self.ck(self._invalid_response))
        else:
            if len(content) == 2:
                key = None
            else:
                key = content[2]
            if self.has_cd(channel, key):
                await ctx.send(self.ck("I'm already counting down!"))
                return
            else:
                await ctx.send(self.ck('Countdown starting...'))
            self._cd[channel]['_base' if key is None else key] = asyncio.create_task(
                self.countdown_helper(
                    ctx, 
                    dt,
                    key=key,
                    )
            )
    
    def has_cd(self, channel, key):
        key = '_base' if key is None else key
        if key not in self._cd[channel]:
            output = False
        elif isinstance(self._cd[channel][key], asyncio.Task):
            output = True
        else:
            output = False
        return output

    def format_time_remain(self, mod_dt, key=None):
        if mod_dt <= 0:
            message = self._countdown_go_text
        else:
            if mod_dt <= 60:
                message = str(mod_dt) + '...'
            elif mod_dt <= 60*5:
                s = str(mod_dt % 60)
                if len(s) == 1:
                    s = '0'+s
                message = str(math.floor(mod_dt/60)) + ':' + s + '...'
        if key is not None:
            message = key + ': ' + message
        return message
    
    async def countdown_helper(self, ctx: commands.Context, duration, key=None):
        await asyncio.sleep(1.1)
        start_time = time.time()
        end_time = start_time + round(duration)
        while True:
            time_now = time.time()
            total_dt = end_time - time_now
            int_dt = round(total_dt)

            # Print the time
            message = self.format_time_remain(int_dt, key=key)
            await ctx.send(self.ck(message))
            #print(message)
            if message == self.format_time_remain(0):
                break

            # Work out the next time
            if round(total_dt) <= 5:
                mod = 1
            elif round(total_dt) <= 30:
                mod = 5
            elif round(total_dt) <= 60:
                mod = 10
            elif round(total_dt) <= 5*60:
                mod = 30
            elif round(total_dt) <= 10*60:
                mod = 60
            dt = total_dt % mod

            if (total_dt - dt) == int_dt:
                dt = mod
                
            adj_dt = max([1.05, dt, 0]) #Make sure the next dt always gives about 1.05s between messages and is not negative

            if adj_dt > dt:
                total_dt = total_dt + (adj_dt - dt)
                dt = adj_dt

            # Wait for the required amount of time
            await asyncio.sleep(dt)

        key = '_base' if key is None else key
        self._cd[ctx.channel.name][key] = None

    def stop_countdown(self, channel, key=None):
        key = '_base' if key is None else key
        if key not in self._cd[channel].keys() or self._cd[channel][key] is None:
            message = "There's no active countdown."
        elif isinstance(self._cd[channel][key], asyncio.Task):
            message = 'Countdown has been cancelled.'
            self._cd[channel][key].cancel()
            self._cd[channel][key] = None
        else:
            message = 'Some weird stuff happened: countdown reset.'
            self._cd[channel][key] = None
        return message

class LevelAdderMixin:
    def __init__(self, level_code_pattern:str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._queue: Dict[str, Dict[str, Union[None, Dict[str, str], List[Dict[str, str]]]]] = {channel:[] for channel in kwargs['initial_channels']}
        self._queue_status: Dict[str, bool] = {channel:False for channel in kwargs['initial_channels']}
        self._level_code_pattern = level_code_pattern
        self._level_history_file = 'level_history.json'
        self._queue_not_open_message = 'The queue is not open.'
        if not os.path.isfile(self._level_history_file):
            with open(self._level_history_file,'w') as f:
                json.dump(
                    {
                        x:{
                            'queue':[],
                            'current':None, 
                            'complete':{},
                            }
                        for x in kwargs['initial_channels']}
                    , f)
        with open(self._level_history_file,'r') as f:
            memory = json.load(f)
            # This is for backward compatibility
            key = list(memory.keys())[0]
            if isinstance(memory[key], str):
                memory = {x:{'current':None, 'queue':[], 'complete':memory} for x in kwargs['initial_channels']}
        self._queue = memory
        self.save_queue()

    def save_queue(self):
        with open(self._level_history_file,'w') as f:
            json.dump(self._queue, f)

    def validate_level_pattern(self, new_code):
        if len(re.findall(self._level_code_pattern.replace('X','[0-9]'), new_code)) > 0:
            return True
        else:
            return False

    def check_played(self, channel, new_code):
        if new_code in self._queue[channel]['complete'].keys():
            message = "I've played this level already."
        elif self._queue[channel]['current'] is not None and new_code in self._queue[channel]['current']['code']:
            message = "I'm playing this level now."
        elif new_code in [x['code'] for x in self._queue[channel]['queue']]:
            message = "The level is already in the queue."
        else:
            message = None
        return message
        
    def add_played(self, channel, new_code):
        self._queue[channel]['complete'][new_code] = datetime.date.today().strftime('%Y-%m-%d')

    @commands.command()
    async def open(self, ctx: commands.Context):
        allowed = False
        allowed = allow_broadcaster(self, ctx, allowed)
        if not allowed:
            message = self._no_permission_response
        else:
            message = self._queue_status[ctx.channel.name] = True
            message = 'The queue is now open'
        await ctx.send(message)

    @commands.command()
    async def close(self, ctx: commands.Context):
        allowed = False
        allowed = allow_broadcaster(self, ctx, allowed)
        if not allowed:
            message = self._no_permission_response
        else:
            message = self._queue_status[ctx.channel.name] = False
            message = 'The queue is now closed'
        await ctx.send(message)

    @commands.command()
    async def add(self, ctx: commands.Context):
        content = ctx.message.content.split(' ')
        channel = ctx.channel.name
        user = ctx.author.name

        if self._queue_status[channel] is False:
            message = self._queue_not_open_message
        elif len(content) != 2:
            message = self._invalid_response
        else:
            level_code = content[1]
            if user in [x['user'] for x in self._queue[channel]['queue']]:
                message = f'You already have a level {user}. Use !replace first to replace your level.'
            else:
                if self.validate_level_pattern(level_code):
                    message = self.check_played(channel, level_code)
                    if message is None:
                        self._queue[channel]['queue'].append({'user':user, 'code':level_code, 'sub':ctx.author.is_subscriber})
                        message = f'Your level has been added {user}'
                else:
                    message = f'Invalid level code: level codes need to look like {self._level_code_pattern}'

        await ctx.send(self.ck(message))
        self.save_queue()

    @commands.command()
    async def replace(self, ctx: commands.Context):
        content = self.parse_content(ctx.message.content)
        channel = ctx.channel.name
        user = ctx.author.name

        if not self._queue_status[channel]:
            message = self._queue_not_open_message
        elif len(content) != 2:
            message = self._invalid_response
        else:
            level_code = content[1]
            message = self.check_played(channel, level_code)
            if message is None:
                if self.validate_level_pattern(level_code):
                    level = {'user':user, 'code':level_code}
                    submitted_users = [x['user'] for x in self._queue[channel]['queue']]
                    if user in submitted_users:
                        idx = submitted_users.index(user)
                        self._queue[channel]['queue'][idx] = level
                        message = f'Your level has been replaced {user}'
                    else:
                        self._queue[channel]['queue'].append(level)
                        message = f'Your level has been added {user}'
                else:
                    message = f'Invalid level code: level codes need to look like {self._level_code_pattern}'
        await ctx.send(self.ck(message))
        self.save_queue()

    @commands.command()
    async def keet(self, ctx: commands.Context):
        allowed = False
        allowed = allow_broadcaster(self, ctx, allowed)
        if not allowed:
            await ctx.send(self.ck(self._no_permission_response))
            return
        content = self.parse_content(ctx.message.content)
        if len(content) == 1:
            content.append(None)
        message = self._select_from_queue(ctx, store=False, which=content[1])
        await ctx.send(self.ck(message))
        self.save_queue()

    @commands.command()
    async def next(self, ctx: commands.Context):
        allowed = False
        allowed = allow_broadcaster(self, ctx, allowed)
        if not allowed:
            await ctx.send(self.ck(self._no_permission_response))
            return
        content = self.parse_content(ctx.message.content)
        if len(content) == 1:
            content.append(None)
        message = self._select_from_queue(ctx, store=True, which=content[1])
        await ctx.send(self.ck(message))
        self.save_queue()

    def _select_from_queue(self, ctx: commands.Context, store:bool, which=None):
        channel = ctx.channel.name
        if self._queue[channel]['current'] is not None and store:
            self.add_played(channel, self._queue[channel]['current']['code'])
        if len(self._queue[channel]['queue']) == 0:
            self._queue[channel]['current'] = None
            return "There's nothing in the queue!"
        else:
            if which is None or which == 'next':
                self._queue[channel]['current'] = self._queue[channel]['queue'][0]
                self._queue[channel]['queue'] = self._queue[channel]['queue'][1:]
            elif which == 'subnext':
                levels = [(ii, x) for ii,x in enumerate(self._queue[channel]['queue']) if x['sub']]
                if len(levels) == 0:
                    return 'There are no sub levels in the queue.'
                else:
                    idx = 0
                    self._queue[channel]['current'] = levels[idx][1]
                    self._queue[channel]['queue'].pop(levels[idx][0])
            elif which == 'random':
                idx = randrange(len(self._queue[channel]))
                self._queue[channel]['current'] = self._queue[channel]['queue'][idx]
                self._queue[channel]['queue'].pop(idx)
            elif which == 'subrandom':
                levels = [(ii, x) for ii,x in enumerate(self._queue[channel]['queue']) if x['sub']]
                if len(levels) == 0:
                    return 'There are no sub levels in the queue'
                else:
                    idx = randrange(levels)
                    self._queue[channel]['current'] = levels[idx][1]
                    self._queue[channel]['queue'].pop(levels[idx][0])
            else:
                return self._invalid_response
            user = self._queue[channel]['current']['user']
            level_code = self._queue[channel]['current']['code']
            return f'{user} your level is up! {level_code}'

    @commands.command()
    async def current(self, ctx: commands.Context):
        if self._queue_status[ctx.channel.name] is False:
            await ctx.send(self._queue_not_open_message)
        elif self._queue[ctx.channel.name]['current'] is None:
            await ctx.send(self.ck("We're not currently playing a level"))
        else:
            user = self._queue[ctx.channel.name]['current']['user']
            level_code = self._queue[ctx.channel.name]['current']['code']
            await ctx.send(self.ck(f'Current level is {level_code} by {user}.'))

    @commands.command()
    async def queue(self, ctx: commands.Context):
        users = [x['user'] for x in self._queue[ctx.channel.name]['queue']]
        message = str(len(self._queue[ctx.channel.name]['queue'])) + ' level in queue : '+', '.join([x['user'] for x in self._queue[ctx.channel.name]['queue']])
        if not self._queue_status[ctx.channel.name]:
            message = self._queue_not_open_message
        elif len(users) == 0:
            message = "The queue is empty."
        await ctx.send(self.ck(message))

    @commands.command()
    async def leave(self, ctx: commands.Context):
        user = ctx.author.name
        channel = ctx.channel.name
        submitted_users = [x['user'] for x in self._queue[channel]['queue']]
        if not self._queue_status[channel]:
            message = self._queue_not_open_message
        elif user in submitted_users:
            idx = submitted_users.index(user)
            self._queue[channel]['queue'].pop(idx)
            message = f'Your level has been removed {user}'
        else:
            message = f"{user} you don't have a level to remove."
        await ctx.send(self.ck(message))
        self.save_queue()

    @commands.command()
    async def clear(self, ctx: commands.Context):
        allowed = False
        allowed = allow_broadcaster(self, ctx, allowed)
        if not allowed:
            await ctx.send(self.ck(self._no_permission_response))
            return
        self._queue[ctx.channel.name]['queue'] = []
        self._queue[ctx.channel.name]['current'] = None
        await ctx.send(self.ck('Queue cleared'))
        self.save_queue()

    @commands.command()
    async def check(self, ctx: commands.Context):
        user = ctx.author.name
        channel = ctx.channel.name
        submitted_users = [x['user'] for x in self._queue[channel]['queue']]
        if not self._queue_status[channel]:
            message = self._queue_not_open_message
        elif user in submitted_users:
            idx = submitted_users.index(user)
            level = self._queue[channel]['queue'][idx]['code']
            idx = idx + 1
            message = f'{user}, you submitted {level}. You are number {idx} in the queue.'
        else:
            message = f"{user} you don't have a level submitted."
        await ctx.send(self.ck(message))

class Bot(commands.Bot):
    def __init__(
        self,
        token: str,
        configs: Dict[str, str],
        *,
        client_secret: str = None,
        initial_channels: Union[list, tuple, Callable] = None,
        loop: asyncio.AbstractEventLoop = None,
        heartbeat: Optional[float] = 30.0,
        retain_cache: Optional[bool] = True,
        refresh_token: Optional[str] = None,
        invalid_response: Optional[str] = None,
        no_permission_response: Optional[str] = None,
        bot_whitelist: List[str] = [],
        **kwargs
    ):
        super().__init__(
            token=token,
            client_secret = client_secret,
            initial_channels = initial_channels,
            loop = loop,
            heartbeat = heartbeat,
            retain_cache = retain_cache,
            **kwargs
            )
        self._http._refresh_token = refresh_token
        self._configs = configs
        self._invalid_response = invalid_response
        self._no_permission_response = no_permission_response
        self._bot_whitelist = bot_whitelist
        self._repeat_preventer = '\U000e0000'
        self._last_message = ''

    def parse_content(self, s):
        return s.strip(self._repeat_preventer).strip().split()

    def ck(self, message):
        if self._last_message == message:
            self._last_message = message + self._repeat_preventer
            return message + self._repeat_preventer
        self._last_message = message
        return message

    async def event_ready(self):
        print(f"{self._configs['BOT_NICK']} is online!")

    @commands.command()
    async def where(self, ctx: commands.Context):
         await ctx.send(self.ck(f'Hello, I am here!'))

    @commands.command()
    async def hello(self, ctx: commands.Context):
        await ctx.send(self.ck(f'Hello {ctx.author.name}!'))

    @commands.command()
    async def add_whitelist(self, ctx: commands.Context):
        allowed = allow_broadcaster(self, ctx)
        allowed = allow_mods(self, ctx, allowed)
        content = self.parse_content(ctx.message.content)
        if not allowed:
            await ctx.send(self.ck(self._no_permission_response))
        elif content[1] not in self._bot_whitelist:
            await ctx.send(self.ck(f"You're cool {content[1]}"))
            self._bot_whitelist.append(content[1])
        else:
            await ctx.send(self.ck(f"{content[1]} is already cool with me!"))

    @commands.command()
    async def remove_whitelist(self, ctx: commands.Context):
        allowed = allow_broadcaster(self, ctx)
        allowed = allow_mods(self, ctx, allowed)
        content = self.parse_content(ctx.message.content)
        if not allowed:
            await ctx.send(self.ck(self._no_permission_response))
        elif content[1] not in self._bot_whitelist:
            await ctx.send(self.ck(f"I wasn't cool with you anyway {content[1]}"))
        else:
            await ctx.send(self.ck(f"You're dead to me {content[1]}!"))
            self._bot_whitelist.remove(content[1])

def create_bot(config, user):
    access_token = twitch_auth.refresh_access_token(config=config, user=user)
    refresh_token = windows_auth.get_refresh_token(config=config, username=user)

    class CustomBot(CountdownMixin, LevelAdderMixin, Bot):
        pass
    bot = CustomBot(
        token=access_token, 
        configs=config,
        client_id=config['CLIENT_ID'], 
        client_secret=config['SECRET'], 
        nick=config['BOT_NICK'], 
        prefix=config['BOT_PREFIX'], 
        initial_channels=config['CHANNELS'],
        refresh_token=refresh_token,
        level_code_pattern=config['LEVEL_CODE_PATTERN'],
        invalid_response=config['INVALID_COMMAND_RESPONSE'],
        no_permission_response=config['NO_PERMISSION_RESPONSE'],
        bot_whitelist=config.get('WHITE_LIST_USERS',[]),
        countdown_go_text=config.get('COUNTDOWN_GO_TEXT',[]),
        )
    return bot