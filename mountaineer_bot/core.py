from typing import Union, Callable, Optional, Dict, List

import time
import asyncio
import math
import re
import json
import datetime
import pytz
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
            await self.send(ctx, self._no_permission_response)
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
                await self.send(ctx, message)
            else:
                if self._invalid_response is not None:
                    await self.send(ctx, self._invalid_response)
        elif dt <= 0:
            if self._invalid_response is not None:
                await self.send(ctx, self._invalid_response)
        else:
            if len(content) == 2:
                key = None
            else:
                key = content[2]
            if self.has_cd(channel, key):
                await self.send(ctx, "I'm already counting down!")
                return
            else:
                await self.send(ctx, 'Countdown starting...')
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
            await self.send(ctx, message)
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
        await self.send(ctx, message)

    @commands.command()
    async def close(self, ctx: commands.Context):
        allowed = False
        allowed = allow_broadcaster(self, ctx, allowed)
        if not allowed:
            message = self._no_permission_response
        else:
            message = self._queue_status[ctx.channel.name] = False
            message = 'The queue is now closed'
        await self.send(ctx, message)

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

        await self.send(ctx, message)
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
        await self.send(ctx, message)
        self.save_queue()

    @commands.command()
    async def keet(self, ctx: commands.Context):
        allowed = False
        allowed = allow_broadcaster(self, ctx, allowed)
        if not allowed:
            await self.send(ctx, self._no_permission_response)
            return
        content = self.parse_content(ctx.message.content)
        if len(content) == 1:
            content.append(None)
        message = self._select_from_queue(ctx, store=False, which=content[1])
        await self.send(ctx, message)
        self.save_queue()

    @commands.command()
    async def next(self, ctx: commands.Context):
        allowed = False
        allowed = allow_broadcaster(self, ctx, allowed)
        if not allowed:
            await self.send(ctx, self._no_permission_response)
            return
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
    async def clear(self, ctx: commands.Context):
        allowed = False
        allowed = allow_broadcaster(self, ctx, allowed)
        if not allowed:
            await self.send(ctx, self._no_permission_response)
            return
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

class SchedulerMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._schedule_file = 'schedule.json'
        self.LIST_COOLDOWN_SECONDS = 20
        if not os.path.isfile(self._schedule_file):
            with open(self._schedule_file,'w') as f:
                json.dump(
                    {
                        x:[]
                        for x in kwargs['initial_channels']}
                    , f)
        with open(self._schedule_file,'r') as f:
            self._schedule: Dict[str, List[List]] = json.load(f)
        self._weekday_map = {
            6: 'Sunday',
            0: 'Monday',
            1: 'Tuesday',
            2: 'Wednesday',
            3: 'Thursday',
            4: 'Friday',
            5: 'Saturday',
        }
        self._dow_conversion = {
            'sunday': 6,
            'sun': 6,
            'monday': 0,
            'mon': 0,
            'tuesday': 1,
            'tues': 1,
            'wednesday': 2,
            'wed': 2,
            'thursday': 3,
            'thurs': 3,
            'friday': 4,
            'fri': 4,
            'saturday': 5,
            'sat': 5
        }
        self.last_list: Dict[str, datetime.datetime] = {}
    
    def _get_current_schedule(self, channel, local_time: datetime.datetime):
        dow = local_time.weekday()
        time = local_time.time()
        current_game = None
        current_game_end = None
        for game_dow, game_start, game_end, game in self._schedule[channel]:
            game_start = datetime.datetime.strptime(game_start, "%H:%M").time()
            game_end = datetime.datetime.strptime(game_end, "%H:%M").time()
            if game_dow == dow and time >= game_start:
                if (game_start > game_end) or (game_start < game_end and time < game_end):
                    current_game = game
                    current_game_end = local_time.replace(hour=game_end.hour, minute=game_end.minute)
            if game_start > game_end and game_dow == ((dow - 1) % 7) and time < game_end:
                current_game = game
                current_game_end = local_time.replace(hour=game_end.hour, minute=game_end.minute) + datetime.timedelta(days=1)
        return current_game, current_game_end

    def _get_next_schedule(self, channel, local_time: datetime.datetime):
        dow = local_time.weekday()
        time = local_time.time().strftime('%H:%M')
        new_item = [dow, time, '', '']
        schedule = sorted([x for x in self._schedule[channel]] + [new_item])
        next_item_idx = (schedule.index(new_item)+1) % len(schedule)
        next_item = schedule[next_item_idx]
        return next_item[-1], next_item[0], next_item[1]

    def _get_schedule(self, channel, tz_name=None, current_time=None):
        if current_time is None:
            current_time = datetime.datetime.now()
        current_time_tz = current_time.astimezone()
        dow_int = current_time.weekday()
        game, current_end_time = self._get_current_schedule(channel, current_time)
        next_game, next_game_dow, next_game_time = self._get_next_schedule(channel, current_time)

        next_game_dt = current_time + datetime.timedelta(days=(next_game_dow - dow_int) % 7)
        next_game_time = datetime.datetime.strptime(next_game_time, '%H:%M')
        next_game_dt = next_game_dt.replace(hour=next_game_time.hour, minute=next_game_time.minute)

        tz_local = ''
        if tz_name is not None:
            if tz_name.lower().startswith('gmt'):
                tz_name_clr = tz_name.lower().replace('gmt','')
                sign = 1 if tz_name_clr[0] == '+' else -1
                try:
                    hr_diff = sign * float(tz_name_clr[1:])
                    dt = datetime.timedelta(hours=hr_diff) - current_time_tz.tzinfo.utcoffset(current_time_tz)
                except ValueError:
                    return "I don't understand the GMT timezone you're asking for. Make sure you enter GMT+XX.XX or GMT-XX.XX"
            else:
                tz_found = [x for x in pytz.all_timezones if tz_name.replace(' ','_').title() in x]
                if len(tz_found) == 0:
                    return 'Cannot determine your timezone. Please enter GMT+X or GMT-X'
                elif len(tz_found) > 1:
                    return 'Your timezone is ambiguous. Please enter GMT+X or GMT-X to be specific'
                tz = pytz.timezone(tz_found[0])
                dt = tz.utcoffset(current_time) - current_time_tz.tzinfo.utcoffset(current_time_tz)
            next_game_dt = next_game_dt + dt
            current_time = current_time + dt
            if current_end_time is not None:
                current_end_time = current_end_time + dt
            tz_local = ' in {}'.format(tz_name)

        if game is not None:
            current_end_time_str = current_end_time.strftime('%I:%M %p')
            game = f' and the game is {game}, ending at {current_end_time_str}'
        else:
            game= ''

        dow = self._weekday_map[current_time.weekday()]
        if next_game_dt.weekday() == current_time.weekday():
            next_game_dow = 'today'
        elif next_game_dt.weekday() == ((current_time.weekday() + 1) % 7):
            next_game_dow = 'tomorrow'
        else:
            next_game_dow = 'on ' + self._weekday_map[next_game_dt.weekday()]
        next_game_time = next_game_dt.time().strftime('%I:%M %p')
        time = current_time.time().strftime('%I:%M %p')

        message = f"It is {dow}, {time}{tz_local}{game}. The next game is {next_game} {next_game_dow} at {next_game_time}"
        return message
    
    def _save_schedule(self):
        with open(self._schedule_file,'w') as f:
            json.dump(self._schedule, f)

    def _add_to_schedule(self, channel: str, start_dow: str, start_time_str: str, end_time_str: str, game: str):
        if start_dow.lower() not in self._dow_conversion.keys():
            return 'Invalid day of week.'
        start_dow = self._dow_conversion[start_dow.lower()]
        try:
            datetime.datetime.strptime(start_time_str, "%H:%M")
        except ValueError:
            return "Start time format should be HH:MM in 24 time."
        try:
            datetime.datetime.strptime(end_time_str, "%H:%M")
        except ValueError:
            return "End time format should be HH:MM in 24 time."
        schedule_start_times = [x[:2] for x in self._schedule[channel]]
        new_item = [start_dow, start_time_str]
        if new_item in schedule_start_times:
            idx = schedule_start_times.index([start_dow, start_time_str])
            existing = self._schedule[channel][idx]
            return f"There is already something on at that time already: {existing[-1]} on {self._weekday_map[existing[0]]} from {existing[1]} to {existing[2]}"
        new_item = [start_dow, start_time_str, end_time_str, game]
        self._schedule[channel].append(new_item)
        self._schedule[channel] = sorted(self._schedule[channel])
        idx = self._schedule[channel].index(new_item)
        next_item = self._schedule[channel][(idx + 1) % len(self._schedule[channel])]
        if new_item[2] == new_item[1]:
            self._schedule[channel].pop(idx)
            return "Why are you ending the game when you've barely started? I'm not adding this to the schedule!"
        elif new_item[2] > new_item[1]:
            new_item_end = [new_item[0], new_item[2]]
        else:
            new_item_end = [(new_item[0]+1) % 7, new_item[2]]
        if (
            len(self._schedule[channel]) > 1 and 
            new_item_end[0] == next_item[0] and 
            new_item_end[1] > next_item[1]
        ):
            self._schedule[channel].pop(idx)
            return f"The end time of the new entry overlaps an entry: {next_item[-1]} on {self._weekday_map[next_item[0]]} from {next_item[1]} to {next_item[2]}. I haven't added the new entry."
        self._save_schedule()
        return "New entry added!"

    def _remove_schedule(self, channel: str, dow: str, time: str):
        dow = self._dow_conversion[dow.lower()]
        rm_list = []
        
        for item in self._schedule[channel]:
            start_time = item[1]
            end_time = item[2]
            if item[2] > item[1]: # When game time doesn't cross into a new day
                if item[0] == dow and start_time <= time and end_time >= time: # If game overlaps target time
                    self._schedule[channel].remove(item)
                    rm_list.append(self._format_item_str(item))
            elif item[2] < item[1]: # When game time does cross into a new day
                if (item[0] == dow and start_time <= time):
                    self._schedule[channel].remove(item)
                    rm_list.append(self._format_item_str(item))
                elif (item[0] == ((dow - 1) % 7)) and end_time >= time:
                    self._schedule[channel].remove(item)
                    rm_list.append(self._format_item_str(item))
        if len(rm_list) == 0:
            message = "I didn't find a scheduled game at the time."
        else:
            message = "Removed " + ' and '.join(rm_list)
        self._save_schedule()
        return message

    def _format_item_str(self, item):
        return f'{item[-1]} : {self._weekday_map[item[0]]} from {item[1]} to {item[2]}'

    async def list_schedule(self, ctx: commands.Context):
        channel = ctx.channel.name
        self.last_list[channel] = datetime.datetime.now()
        if len(self._schedule[channel]) == 0:
            await self.send(ctx, "There's nothing on the schedule!")
            return
        for item in self._schedule[channel]:
            await self.send(ctx, self._format_item_str(item))
            await asyncio.sleep(1.1)
        return

    @commands.command()
    async def schedule(self, ctx: commands.Context):
        channel = ctx.channel.name
        content = ctx.message.content.strip(self._repeat_preventer).strip().split(' ')
        if len(content) == 1:
            message = self._get_schedule(channel)
        else:
            command = content[1]
            if command == 'add':
                allowed = False
                allowed = allow_broadcaster(self, ctx, allowed)
                if not allowed:
                    await self.send(ctx, self._no_permission_response)
                    return
                if len(content) < 6:
                    message = 'Not enough arguments: !schedule add [start day of week] [start 24hr time] [end 24hr time] [Game]'
                else:
                    game = ' '.join(content[5:])
                    content = content[:6]
                    content[5] = game
                    message = self._add_to_schedule(channel, *content[2:])
            elif content[1] == 'list':
                last_list = self.last_list.get(channel)
                if last_list is not None and ((datetime.datetime.now() - last_list).total_seconds() <= self.LIST_COOLDOWN_SECONDS):
                    await self.send(ctx, "I just did this. Wait a bit before trying again.")
                else:
                    asyncio.create_task(
                        self.list_schedule(ctx)
                    )
                return
            elif command == 'remove':
                allowed = False
                allowed = allow_broadcaster(self, ctx, allowed)
                if not allowed:
                    await self.send(ctx, self._no_permission_response)
                    return
                if len(content) < 4:
                    message = 'Not enough arguments: !schedule remove [day of week] [24hr time]'
                else:
                    content[2] = content[2]
                    message = self._remove_schedule(channel, *content[2:])
            else:
                message = self._get_schedule(channel, tz_name=' '.join(content[1:]))
        if message is not None:
            await self.send(ctx, message)


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

    async def send(self, ctx, message):
        await ctx.send(self.ck(message))
        return


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
         await self.send(ctx, f'Hello, I am here!')

    @commands.command()
    async def hello(self, ctx: commands.Context):
        await self.send(ctx, f'Hello {ctx.author.name}!')

    @commands.command()
    async def add_whitelist(self, ctx: commands.Context):
        allowed = allow_broadcaster(self, ctx)
        allowed = allow_mods(self, ctx, allowed)
        content = self.parse_content(ctx.message.content)
        if not allowed:
            await self.send(ctx, self._no_permission_response)
        elif content[1] not in self._bot_whitelist:
            await self.send(ctx, f"You're cool {content[1]}")
            self._bot_whitelist.append(content[1])
        else:
            await self.send(ctx, f"{content[1]} is already cool with me!")

    @commands.command()
    async def remove_whitelist(self, ctx: commands.Context):
        allowed = allow_broadcaster(self, ctx)
        allowed = allow_mods(self, ctx, allowed)
        content = self.parse_content(ctx.message.content)
        if not allowed:
            await self.send(ctx, self._no_permission_response)
        elif content[1] not in self._bot_whitelist:
            await self.send(ctx, f"I wasn't cool with you anyway {content[1]}")
        else:
            await self.send(ctx, f"You're dead to me {content[1]}!")
            self._bot_whitelist.remove(content[1])

def create_bot(config, user):
    access_token = twitch_auth.refresh_access_token(config=config, user=user)
    refresh_token = windows_auth.get_refresh_token(config=config, username=user)

    class CustomBot(CountdownMixin, LevelAdderMixin, SchedulerMixin, Bot):
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