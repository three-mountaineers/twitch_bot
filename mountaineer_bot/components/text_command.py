from typing import Optional, Dict, TypedDict,  NotRequired, Literal
import os
import logging
import json
import asyncio
import random

from twitchio.ext import commands, routines
from twitchio.message import Message

from mountaineer_bot import BotMixin, BotEventMixin, api
from mountaineer_bot.tw_events.types import StreamOffline, StreamOnline, GoalBegin, GoalEnd
from mountaineer_bot.security import restrict_command, restrict_message

class Commands(TypedDict):
    count: NotRequired[int]
    type: Literal['counter','command']
    text: str
    repeat: NotRequired[Optional[float]]

class TextCommand(BotMixin):
    _required_scope = [
        'chat:read',
        'chat:edit',
    ]
    _text_command_cache: dict[str, dict[str, Commands]]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._text_command_file = os.path.join(self._appdir.user_config_dir, 'text_command_cache.json')
        if not os.path.isfile(self._text_command_file):
            with open(self._text_command_file,'w') as f:
                json.dump({}, f)
        with open(self._text_command_file,'r') as f:
            self._text_command_cache = json.load(f)
            for channel in self._channels:
                if channel not in self._text_command_cache.keys():
                    self._text_command_cache[channel] = {}

    def save(self):
        with open(self._text_command_file,'w') as f:
            json.dump(self._text_command_cache, f)

    def has_count(self, channel:str, key:str):
        return key in self._text_command_cache[channel]

    def add_count(self, channel:str, key:str):
        if key not in self._text_command_cache[channel]:
            return
        if self._text_command_cache[channel][key]['type'] == 'counter':
            self._text_command_cache[channel][key]['count'] += 1
            self.save()

    def set_count(self, channel:str, key:str, count: int):
        self._text_command_cache[channel][key]['count'] = count
        self.save()

    def replace_text(self, channel:str, key:str, text: str):
        if key not in self._text_command_cache[channel]:
            return f"{key} couldn't be found"
        elif isinstance(self._text_command_cache[channel][key], dict): # Counter
            if '{count}' in text:
                self._text_command_cache[channel][key]['text'] = text
            else:
                return "Couldn't replace counter text since it's missing a '{count}'"
        else:
            self._text_command_cache[channel][key]['text'] = text
        return f"Text for command '{key}' replaced"

    def check_command(self, channel:str, key:str):
        if key not in self._text_command_cache[channel]:
            return
        if self._text_command_cache[channel][key]['type'] == 'counter':
            text = self._text_command_cache[channel][key]['text']
            count = self._text_command_cache[channel][key]['count']
            text = text.format(count=count)
        else:
            text = self._text_command_cache[channel][key]['text']
        return text

    def new_counter(self, channel:str, key:str, text:str, repeat: Optional[float]):
        if key in self._text_command_cache[channel]:
            return f'Command "{key}" already exists.'
        elif '{count}' not in text:
            return 'The text string needs to have "{count}" somewhere in it.'
        else:
            self._text_command_cache[channel][key] = {
                'text': text,
                'count': 0,
                'type': 'counter',
                'repeat': repeat,
            }
            self.save()
            return self.check_command(channel, key)

    def new_command(self, channel:str, key:str, text:str, repeat: Optional[float]):
        if key in self._text_command_cache[channel]:
            return f'Command "{key}" already exists.'
        else:
            self._text_command_cache[channel][key] = {'text': text, 'repeat': repeat, 'type': 'command'}
            self.save()
            return text

    @restrict_message(default=True, live_only=False)
    async def event_message(self, message: Message):
        await super().event_message(message=message)
        channel = message.channel
        if message.content[0] == self._prefix:
            args = message.content.split(' ')
            counter_key = args[0][1:]
            if len(args) == 1:
                self.add_count(channel.name, counter_key)
            text = self.check_command(channel.name, counter_key)
            if text is not None:
                await self.send(channel.name, text)

    @commands.command()
    @restrict_command()
    async def counter_register(self, ctx: commands.Context):
        args = self.parse_content(ctx.message.content)
        if len(args) < 3:
            await self.send(ctx.channel.name, "Can't add counter, need the new count command and message as arguments")
        else:
            key = args[1]
            try:
                repeat = float(args[2])
                text = ' '.join(args[3:])
            except ValueError:
                repeat = None
                text = ' '.join(args[2:])
            return_text = self.new_counter(ctx.channel.name, key, text, repeat)
            await self.send(ctx.channel.name, return_text)

    @commands.command()
    @restrict_command()
    async def counter_remove(self, ctx: commands.Context):
        args = self.parse_content(ctx.message.content)
        if len(args) < 2:
            await self.send(ctx.channel.name, "Can't remove counter. Counter key needs to be passed as an argument.")
        key = args[1]
        if key not in self._text_command_cache[ctx.channel.name]:
            await self.send(ctx.channel.name, f"Counter '{key}' couldn't be found.")
        else:
            self._text_command_cache[ctx.channel.name].pop(key)
            await self.send(ctx.channel.name, f'Counter "{key}" removed.')

    @commands.command()
    @restrict_command()
    async def counter_reset(self, ctx: commands.Context):
        args = self.parse_content(ctx.message.content)
        if len(args) < 2:
            await self.send(ctx.channel.name, "Command to reset missing")
        else:
            key = args[1]
            if not self.has_count(ctx.channel.name, key):
                await self.send(ctx.channel.name, f"{key} isn't registered as a count ")
            old_count = self._text_command_cache[ctx.channel.name][key]['count']
            if len(args) == 3:
                if not args[2].isnumeric():
                    await self.send(ctx.channel.name, "Can't reset counter, second argument should be a positive integer.")
                new_counter = int(args[2])
            else:
                new_counter = 0
            self.set_count(ctx.channel.name, key, new_counter)
            await self.send(ctx.channel.name, f'Counter {key} of {old_count} is reset to {new_counter}.')

    @commands.command()
    @restrict_command()
    async def counter_check(self, ctx: commands.Context):
        counters = [key for key,val in self._text_command_cache[ctx.channel.name].items() if val['type'] == 'counter']
        registered = ', '.join(counters)
        await self.send(ctx.channel.name, f'The following counters are registered: {registered}')

    @commands.command()
    @restrict_command()
    async def counter_replace_text(self, ctx: commands.Context):
        args = self.parse_content(ctx.message.content)
        if len(args) < 3:
            await self.send(ctx.channel.name, "Command and/or replacement text missing")
        else:
            key = args[1]
            text = ' '.join(args[2:])
            await self.send(ctx.channel.name, self.replace_text(ctx.channel.name, key, text))

    @commands.command()
    @restrict_command()
    async def command_register(self, ctx: commands.Context):
        args = self.parse_content(ctx.message.content)
        if len(args) < 3:
            await self.send(ctx.channel.name, "Can't add command, need the new command and message as arguments")
        key = args[1]
        try:
            repeat = float(args[2])
            text = ' '.join(args[3:])
        except ValueError:
            text = ' '.join(args[2:])
            repeat = None
        return_text = self.new_command(ctx.channel.name, key, text, repeat)
        await self.send(ctx.channel.name, return_text)

    @commands.command()
    @restrict_command()
    async def command_remove(self, ctx: commands.Context):
        args = self.parse_content(ctx.message.content)
        if len(args) < 2:
            await self.send(ctx.channel.name, "Can't remove command. Command key needs to be passed as an argument.")
        key = args[1]
        if key not in self._text_command_cache[ctx.channel.name]:
            await self.send(ctx.channel.name, f"Command '{key}' couldn't be found.")
        else:
            self._text_command_cache[ctx.channel.name].pop(key)
            await self.send(ctx.channel.name, f'Command "{key}" removed.')

    @commands.command()
    @restrict_command()
    async def command_replace(self, ctx: commands.Context):
        args = self.parse_content(ctx.message.content)
        if len(args) < 3:
            await self.send(ctx.channel.name, "Command and/or replacement text missing")
        else:
            key = args[1]
            text = ' '.join(args[2:])
            await self.send(ctx.channel.name, self.replace_text(ctx.channel.name, key, text))

    @commands.command()
    @restrict_command()
    async def command_check(self, ctx: commands.Context):
        counters = [
            key for key,val in self._text_command_cache[ctx.channel.name].items() 
            if val['type'] == 'command'
        ]
        registered = ', '.join(counters)
        await self.send(ctx.channel.name, f'The following commands are registered: {registered}')


class TextCommandRepeat(TextCommand, BotEventMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dummy_is_live = {c.name: False for c in self.connected_channels}
        self.tws.subscriptions += [
            {
                'event': 'stream.online',
                'version': '1',
                'condition': {
                    'broadcaster_user_id': api.get_user_id(self._config['TWITCH_BOT'], channel)
                }
            }
            for channel in self._channels
        ] + [
            {
                'event': 'stream.offline',
                'version': '1',
                'condition': {
                    'broadcaster_user_id': api.get_user_id(self._config['TWITCH_BOT'], channel)
                }
            }
            for channel in self._channels
        ]     

    async def run_loop(self, channel: str, key: str):
        initial_delay = random.randint(0, 100)/100
        delay = self._text_command_cache[channel][key]['repeat']
        assert delay is not None
        await asyncio.sleep(delay*60*initial_delay)
        while self.is_live(channel):
            text = self.check_command(channel, key)
            await self.send(channel, text)
            await asyncio.sleep(delay*60)

    def stream_online(self, message: StreamOnline, version: str):
        for command_name, commands in self._text_command_cache.get(message['broadcaster_user_login'], {}).items():
            if commands['repeat'] is None:
                continue
            asyncio.create_task(self.run_loop(message['broadcaster_user_login'], command_name))
        super().stream_online(message, version)