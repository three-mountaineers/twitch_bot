from typing import Optional, Dict, TypedDict
import logging
import os
import time
import json
import yaml
import asyncio

from playsound import playsound

from twitchio.ext import commands, routines
from twitchio.message import Message

from mountaineer_bot import BotEventMixin, utils
from mountaineer_bot.security import restrict_command

class SoundItem(TypedDict):
    sound_file: str
    priority: int
    order: utils.NotRequired[int]

class SoundReactor(BotEventMixin):
    def __init__(self, *args, **kwargs):
        self.add_required_scope([
            'chat:read','chat:edit',
        ])
        super().__init__(*args, **kwargs)
        self._sound_reactor_config_file = os.path.join(self._appdir.user_config_dir, 'sound_reactor_config.yml')
        if not os.path.isfile(self._sound_reactor_config_file):
            with open(self._sound_reactor_config_file,'w') as f:
                yaml.dump({'command': {"test":"test"}, 'pattern': {"test":"test"}, 'redeem': {"test":"test"}}, f)
        self._sound_queue: list[SoundItem] = []
        self._sound_queue_routine: None | asyncio.Task = None
        self.tws.subscriptions += [
            {
                'event': 'channel.channel_points_custom_reward_redemption.add',
                'version': '1',
                'condition': {
                    'broadcaster_user_id': str(self.tws.user_id),
                },
            }
        ]
        self._idx = 0
        self.load_config()
        self.setup_websocket() 

    def setup_websocket(self):
        pass

    def load_config(self):
        with open(self._sound_reactor_config_file,'r') as f:
            self.sound_reactor_config = yaml.load(f, Loader=yaml.SafeLoader)

    async def play_sound(self):
        while len(self._sound_queue) > 0:
            self._sound_queue = list(sorted(self._sound_queue, key=lambda x: (x['priority'], x['order'])))
            new_sonds = self._sound_queue.pop(0)
            playsound(new_sonds['sound_file'])
            await asyncio.sleep(1.1)
        
    def add_sound(self, sound: SoundItem):
        self._idx += 1
        sound['order'] = self._idx
        self._sound_queue.append(sound)
        if self._sound_queue_routine is None:
            self._sound_queue_routine = asyncio.create_task(self.play_sound())
        elif self._sound_queue_routine.done():
            self._sound_queue_routine = asyncio.create_task(self.play_sound())

    @restrict_command(default=True, live_only=True)
    async def event_message(self, message: Message):
        await super().event_message(message=message)
        if message.author is None:
            return
        if message.content.startswith(self._prefix):
            command_str = message.content[1:].lower().split(' ')[0]
            if command_str in self.sound_reactor_config['command']:
                self.add_sound({
                    'sound_file': self.sound_reactor_config['command'][command_str],
                    'priority': 1,
                })
        else:
            message_words = set(message.content.lower().split(' '))
            sounds = set(self.sound_reactor_config['pattern'].keys()) & message_words
            for sound in sounds:
                self.add_sound({
                    'sound_file': self.sound_reactor_config['pattern'][sound],
                    'priority': 2,
                })

    @commands.command()
    @restrict_command(default=True, live_only=True)
    async def sounds(self, ctx: commands.Context):
        commands = 'Sound commands: ' +  ', '.join(['!'+x for x in self.sound_reactor_config['command'].keys()])
        await self.send(ctx.channel.name, message=commands)
        reacts = 'Sound reacts: ' +  ', '.join([x for x in self.sound_reactor_config['pattern'].keys()])
        await self.send(ctx.channel.name, message=reacts)

    @commands.command()
    @restrict_command(default=False, live_only=True, allowed=['Broadcaster'])
    async def sounds_refresh(self, ctx: commands.Context):
        self.load_config()
        logging.info('SoundReactor catalog refreshed.')
        
    def channel_channel_points_automatic_reward_redemption_add(self, message_dict):
        super().channel_channel_points_automatic_reward_redemption_add(message_dict)
        if message_dict['reward']['id'] in self.sound_reactor_config['redeem']:
            self.add_sound({
                'sound_file': self.sound_reactor_config['redeem'][message_dict['reward']['id']],
                'priority': 0,
            })