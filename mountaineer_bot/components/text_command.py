from typing import Optional, Dict
import os
import logging
import json

from twitchio.ext import commands, routines
from twitchio.message import Message

from mountaineer_bot import BotMixin
from mountaineer_bot.security import restrict_command, restrict_message

class TextCommand(BotMixin):
    _required_scope = [
        'chat:read',
        'chat:edit',
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._text_command_file = os.path.join(self._config_dir, 'text_command_cache.json')
        if not os.path.isfile(self._text_command_file):
            with open(self._text_command_file,'w') as f:
                json.dump({}, f)
        with open(self._text_command_file,'r') as f:
            self._text_command_cache = json.load(f)
            for channel in self._config['CHANNELS']:
                if channel not in self._text_command_cache.keys():
                    self._text_command_cache[channel] = {}

    def save(self):
        with open(self._text_command_file,'w') as f:
            json.dump(self._text_command_cache, f)

    def has_count(self, channel:str, key:str):
        return key in self._text_command_cache[channel]

    def add_count(self, channel:str, key:str):
        if isinstance(self._text_command_cache[channel][key], dict):
            self._text_command_cache[channel][key]['count'] += 1
            self.save()

    def set_count(self, channel:str, key:str, count: int):
        self._text_command_cache[channel][key]['count'] = count
        self.save()

    def replace_text(self, channel:str, key:str, text: int):
        if key not in self._text_command_cache[channel]:
            return f"{key} couldn't be found"
        elif isinstance(self._text_command_cache[channel][key], dict): # Counter
            if '{count}' in text:
                self._text_command_cache[channel][key]['text'] = text
            else:
                return "Couldn't replace counter text since it's missing a '{count}'"
        else:
            self._text_command_cache[channel][key] = text
        return f"Text for command '{key}' replaced"

    def check_command(self, channel:str, key:str):
        if isinstance(self._text_command_cache[channel][key], dict):
            text = self._text_command_cache[channel][key]['text']
            count = self._text_command_cache[channel][key]['count']
            text = text.format(count=count)
        else:
            text = self._text_command_cache[channel][key]
        return text

    def new_counter(self, channel:str, key:str, text:str):
        if key in self._text_command_cache[channel]:
            return f'Command "{key}" already exists.'
        elif '{count}' not in text:
            return 'The text string needs to have "{count}" somewhere in it.'
        else:
            self._text_command_cache[channel][key] = {
                'text': text,
                'count': 0,
            }
            self.save()
            return self.check_command(channel, key)

    def new_command(self, channel:str, key:str, text:str):
        if key in self._text_command_cache[channel]:
            return f'Command "{key}" already exists.'
        else:
            self._text_command_cache[channel][key] = text
            self.save()
            return text

    @restrict_message(default=True, live_only=True)
    async def event_message(self, message: Message):
        await super().event_message(message=message)
        channel = message.channel
        if message.content[0] == '!':
            args = message.content.split(' ')
            counter_key = args[0][1:]
            if counter_key in dir(self):
                return
            if not self.has_count(channel.name, counter_key):
                return
            if len(args) == 1:
                self.add_count(channel.name, counter_key)
                text = self.check_command(channel.name, counter_key)
                await channel.send(text)
            elif args[1] == 'check':
                text = self.check_command(channel.name, counter_key)
                await channel.send(text)

    @commands.command()
    @restrict_command()
    async def counter_register(self, ctx: commands.Context):
        args = self.parse_content(ctx.message.content)
        print(len(args))
        if len(args) < 3:
            print('send')
            await self.send(ctx, "Can't add counter, need the new count command and message as arguments")
            print('sent')
        else:
            key = args[1]
            text = ' '.join(args[2:])
            return_text = self.new_counter(ctx.channel.name, key, text)
            await self.send(ctx, return_text)

    @commands.command()
    @restrict_command()
    async def counter_remove(self, ctx: commands.Context):
        args = self.parse_content(ctx.message.content)
        if len(args) < 2:
            await self.send(ctx, "Can't remove counter. Counter key needs to be passed as an argument.")
        key = args[1]
        if key not in self._text_command_cache[ctx.channel.name]:
            await self.send(ctx, f"Counter '{key}' couldn't be found.")
        else:
            self._text_command_cache[ctx.channel.name].pop(key)
            await self.send(ctx, f'Counter "{key}" removed.')

    @commands.command()
    @restrict_command()
    async def counter_reset(self, ctx: commands.Context):
        args = self.parse_content(ctx.message.content)
        if len(args) < 2:
            await self.send(ctx, "Command to reset missing")
        else:
            key = args[1]
            if not self.has_count(ctx.channel.name, key):
                await self.send(f"{key} isn't registered as a count ")
            old_count = self._text_command_cache[ctx.channel.name][key]['count']
            if len(args) == 3:
                if not args[2].isnumeric():
                    await self.send(ctx, "Can't reset counter, second argument should be a positive integer.")
                new_counter = int(args[2])
            else:
                new_counter = 0
            self.set_count(ctx.channel.name, key, new_counter)
            await self.send(ctx, f'Counter {key} of {old_count} is reset to {new_counter}.')

    @commands.command()
    @restrict_command()
    async def counter_check(self, ctx: commands.Context):
        counters = [key for key,val in self._text_command_cache[ctx.channel.name].items() if isinstance(val, dict)]
        registered = ', '.join(counters)
        await self.send(ctx, f'The following counters are registered: {registered}')

    @commands.command()
    @restrict_command()
    async def counter_replace_text(self, ctx: commands.Context):
        args = self.parse_content(ctx.message.content)
        if len(args) < 3:
            await self.send(ctx, "Command and/or replacement text missing")
        else:
            key = args[1]
            text = ' '.join(args[2:])
            await self.send(ctx, self.replace_text(ctx.channel.name, key, text))

    @commands.command()
    @restrict_command()
    async def command_register(self, ctx: commands.Context):
        args = self.parse_content(ctx.message.content)
        if len(args) < 3:
            await self.send(ctx, "Can't add command, need the new command and message as arguments")
        key = args[1]
        text = ' '.join(args[2:])
        return_text = self.new_command(ctx.channel.name, key, text)
        await self.send(ctx, return_text)

    @commands.command()
    @restrict_command()
    async def command_remove(self, ctx: commands.Context):
        args = self.parse_content(ctx.message.content)
        if len(args) < 2:
            await self.send(ctx, "Can't remove command. Command key needs to be passed as an argument.")
        key = args[1]
        if key not in self._text_command_cache[ctx.channel.name]:
            await self.send(ctx, f"Command '{key}' couldn't be found.")
        else:
            self._text_command_cache[ctx.channel.name].pop(key)
            await self.send(ctx, f'Command "{key}" removed.')

    @commands.command()
    @restrict_command()
    async def command_replace(self, ctx: commands.Context):
        args = self.parse_content(ctx.message.content)
        if len(args) < 3:
            await self.send(ctx, "Command and/or replacement text missing")
        else:
            key = args[1]
            text = ' '.join(args[2:])
            await self.send(ctx, self.replace_text(ctx.channel.name, key, text))

    @commands.command()
    @restrict_command()
    async def command_check(self, ctx: commands.Context):
        counters = [
            key for key,val in self._text_command_cache[ctx.channel.name].items() 
            if isinstance(val, str)
        ]
        registered = ', '.join(counters)
        await self.send(ctx, f'The following commands are registered: {registered}')