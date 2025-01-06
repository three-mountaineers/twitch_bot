from typing import Dict, List
import datetime
import pytz
import os
import json
import asyncio

from twitchio.ext import commands

from mountaineer_bot import BotMixin
from mountaineer_bot.security import restrict_command

class SchedulerMixin(BotMixin):
    def __init__(self, *args, **kwargs):
        self.add_required_scope([
            'chat:read',
            'chat:edit',
        ])
        super().__init__(*args, **kwargs)
        self._schedule_file = os.path.join(self._appdir.user_config_dir, 'schedule.json')
        self.LIST_COOLDOWN_SECONDS = 300
        if not os.path.isfile(self._schedule_file):
            with open(self._schedule_file,'w') as f:
                json.dump(
                    {
                        x:[]
                        for x in self._channels
                    },
                    f
                )
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
    
    @commands.command()
    async def schedule(self, ctx: commands.Context):
        channel = ctx.channel.name
        content = ctx.message.content.strip(self._repeat_preventer).strip().split(' ')
        if len(content) == 1:
            message = self._get_schedule(channel)
            await self.send(ctx, message)
        else:
            command = content[1]
            if command == 'add':
                await self._schedule_add(ctx, content)
            elif content[1] == 'list':
                await self._schedule_list(ctx)
            elif command == 'remove':
                await self._schedule_remove(ctx, content)
            else:
                message = self._get_schedule(channel, tz_name=' '.join(content[1:]))
                await self.send(ctx, message)

    @restrict_command(['Broadcaster'])
    async def _schedule_add(self, ctx: commands.Context, content: List[str]):
        channel = ctx.channel.name
        if len(content) < 6:
            message = 'Not enough arguments: !schedule add [start day of week] [start 24hr time] [end 24hr time] [Game]'
        else:
            game = ' '.join(content[5:])
            content = content[:6]
            content[5] = game
            message = self._add_to_schedule(channel, *content[2:])
        await self.send(ctx, message)

    async def _schedule_list(self, ctx: commands.Context):
        channel = ctx.channel.name
        last_list = self.last_list.get(channel)
        time_since_last = int(round(datetime.datetime.now() - last_list).total_seconds())
        if last_list is not None and (time_since_last <= self.LIST_COOLDOWN_SECONDS) and not ctx.author.is_broadcaster:
            await self.send(ctx, f"I just did this. Wait a bit ({time_since_last}s) before trying again.")
        else:
            asyncio.create_task(
                self._list_schedule(ctx)
            )

    @restrict_command(['Broadcaster'])
    async def _schedule_remove(self, ctx: commands.Context, content):
        channel = ctx.channel.name
        if len(content) < 4:
            message = 'Not enough arguments: !schedule remove [day of week] [24hr time]'
        else:
            content[2] = content[2]
            message = self._remove_schedule(channel, *content[2:])
        await self.send(ctx, message)

    async def _list_schedule(self, ctx: commands.Context):
        channel = ctx.channel.name
        self.last_list[channel] = datetime.datetime.now()
        if len(self._schedule[channel]) == 0:
            await self.send(ctx, "There's nothing on the schedule!")
            return
        for item in self._schedule[channel]:
            await self.send(ctx, self._format_item_str(item))
        return

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
        return f'{self._weekday_map[item[0]]} - {item[-1]} - {item[1]} to {item[2]}'