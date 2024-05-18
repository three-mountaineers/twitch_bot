from typing import Dict, Union, List
import os
import json
import re
import datetime
from random import randrange

from twitchio.ext import commands

from mountaineer_bot import BotMixin
from mountaineer_bot.security import restrict_command

class LevelAdderMixin(BotMixin):
    _required_scope = [
        'chat:read',
        'chat:edit',
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._queue: Dict[str, Dict[str, Union[None, Dict[str, str], List[Dict[str, str]]]]] = {channel:[] for channel in self._config['CHANNELS']}
        self._queue_status: Dict[str, bool] = {channel:False for channel in self._config['CHANNELS']}
        self._level_code_pattern = self._config['LEVEL_CODE_PATTERN']
        self._level_history_file = os.path.join(self._config_dir, 'level_history.json')
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
                        for x in self._config['CHANNELS']}
                    , f)
        with open(self._level_history_file,'r') as f:
            memory = json.load(f)
            # This is for backward compatibility
            key = list(memory.keys())[0]
            if isinstance(memory[key], str):
                memory = {x:{'current':None, 'queue':[], 'complete':memory} for x in self._config['CHANNELS']}
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
        #if new_code in self._queue[channel]['complete'].keys():
        #    message = "I've played this level already."
        if self._queue[channel]['current'] is not None and new_code in self._queue[channel]['current']['code']:
            message = "I'm playing this level now."
        elif new_code in [x['code'] for x in self._queue[channel]['queue']]:
            message = "The level is already in the queue."
        else:
            message = None
        return message
        
    def add_played(self, channel, new_code):
        return
        self._queue[channel]['complete'][new_code] = datetime.date.today().strftime('%Y-%m-%d')

    @commands.command()
    @restrict_command()
    async def open(self, ctx: commands.Context):
        message = self._queue_status[ctx.channel.name] = True
        message = 'The queue is now open'
        await self.send(ctx, message)

    @commands.command()
    @restrict_command()
    async def close(self, ctx: commands.Context):
        message = self._queue_status[ctx.channel.name] = False
        message = 'The queue is now closed'
        await self.send(ctx, message)

    @commands.command()
    @restrict_command(default=True)
    async def add(self, ctx: commands.Context):
        content = self.parse_content(ctx.message.content)
        channel = ctx.channel.name
        user = ctx.author.name

        if self._queue_status[channel] is False:
            message = self._queue_not_open_message
        elif len(content) != 2:
            message = self._invalid_response
        else:
            level_code = content[1].replace(self._repeat_preventer,'')
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
        await self.send(ctx, message)
        self.save_queue()

    @commands.command()
    @restrict_command(default=True)
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
        await self.send(ctx, message)
        self.save_queue()

    async def skip(self, ctx: commands.Context):
        await self.keet(ctx=ctx)

    @commands.command()
    @restrict_command()
    async def keet(self, ctx: commands.Context):
        content = self.parse_content(ctx.message.content)
        if len(content) == 1:
            content.append(None)
        message = self._select_from_queue(ctx, store=False, which=content[1])
        await self.send(ctx, message)
        self.save_queue()

    @commands.command()
    @restrict_command()
    async def next(self, ctx: commands.Context):
        content = self.parse_content(ctx.message.content)
        if len(content) == 1:
            content.append(None)
        message = self._select_from_queue(ctx, store=True, which=content[1])
        await self.send(ctx, message)
        self.save_queue()

    def _select_from_queue(self, ctx: commands.Context, store:bool, which=None):
        channel = ctx.channel.name
        if self._queue[channel]['current'] is not None and store:
            self.add_played(channel, self._queue[channel]['current']['code'])
        if len(self._queue[channel]['queue']) == 0:
            self._queue[channel]['current'] = None
            return f"There's nothing in the queue! @{ctx.channel.name}"
        else:
            if which is None or which == 'next':
                self._queue[channel]['current'] = self._queue[channel]['queue'][0]
                self._queue[channel]['queue'] = self._queue[channel]['queue'][1:]
            elif which == 'subnext':
                levels = [(ii, x) for ii,x in enumerate(self._queue[channel]['queue']) if x['sub']]
                if len(levels) == 0:
                    return f'There are no sub levels in the queue. @{ctx.channel.name}'
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
                    return f'There are no sub levels in the queue. @{ctx.channel.name}'
                else:
                    idx = randrange(levels)
                    self._queue[channel]['current'] = levels[idx][1]
                    self._queue[channel]['queue'].pop(levels[idx][0])
            else:
                return self._invalid_response
            user = self._queue[channel]['current']['user']
            level_code = self._queue[channel]['current']['code']
            return f'{user} your level is up! {level_code} @{ctx.channel.name}'

    @commands.command()
    async def current(self, ctx: commands.Context):
        if self._queue[ctx.channel.name]['current'] is None:
            message = "We're not currently playing a level"
        else:
            user = self._queue[ctx.channel.name]['current']['user']
            level_code = self._queue[ctx.channel.name]['current']['code']
            message = f'Current level is {level_code} by {user}.'
        await self.send(ctx, message)

    @commands.command()
    async def queue(self, ctx: commands.Context):
        users = [x['user'] for x in self._queue[ctx.channel.name]['queue']]
        message = str(len(self._queue[ctx.channel.name]['queue'])) + ' level in queue : '+', '.join([x['user'] for x in self._queue[ctx.channel.name]['queue']])
        if not self._queue_status[ctx.channel.name] and len(users) == 0:
            message = "The queue is empty and closed."
        elif len(users) == 0:
            message = "The queue is empty."
        await self.send(ctx, message)

    @commands.command()
    async def list(self, ctx: commands.Context):
        await self.queue(ctx)

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
        await self.send(ctx, message)
        self.save_queue()

    @commands.command()
    @restrict_command()
    async def clear(self, ctx: commands.Context):
        self._queue[ctx.channel.name]['queue'] = []
        self._queue[ctx.channel.name]['current'] = None
        await self.send(ctx, 'Queue cleared')
        self.save_queue()

    @commands.command()
    async def position(self, ctx: commands.Context):
        await self.check(ctx)

    @commands.command()
    async def check(self, ctx: commands.Context):
        user = ctx.author.name
        channel = ctx.channel.name
        submitted_users = [x['user'] for x in self._queue[channel]['queue']]
        if user in submitted_users:
            idx = submitted_users.index(user)
            level = self._queue[channel]['queue'][idx]['code']
            idx = idx + 1
            message = f'{user}, you submitted {level}. You are number {idx} in the queue.'
        elif not self._queue_status[channel]:
            message = self._queue_not_open_message
        else:
            message = f"{user} you don't have a level submitted."
        await self.send(ctx, message)