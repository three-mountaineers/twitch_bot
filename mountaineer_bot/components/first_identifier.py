from typing import Dict, List, TypedDict
import os
import json
import datetime
import asyncio
import copy

from twitchio.ext import commands
from twitchio.message import Message

from mountaineer_bot import api
from mountaineer_bot.components.stream_live import StreamLiveEventListener
from mountaineer_bot.security import restrict_message

class FirstIdentifierDict(TypedDict):
    last_redeem: str
    score: dict[str, int]

class FirstIdentifier(StreamLiveEventListener):
    _first_identifier_history: Dict[str, FirstIdentifierDict]
    _first_identifier_history_file: str

    def __init__(self, *args, **kwargs):
        self.add_required_scope([
            'chat:read', 
            'chat:edit', 
        ])
        super().__init__(*args, **kwargs)
        
        if 'FIRST_IDENTIFIER' not in self._config:
            self._config['FIRST_IDENTIFIER'] = {
                'MODE': None,
                'TEXT': None,
            }
        while self._config['FIRST_IDENTIFIER']['MODE'] not in ('chat','redeem'):
            self._config['FIRST_IDENTIFIER']['MODE'] = input('[FirstIdentifier] Which way should we identify first chatters? (Chat/Redeem) >').lower()
            if self._config['FIRST_IDENTIFIER']['MODE'] not in ('chat','redeem'):
                print('Invalid input. Must be one of CHAT or REDEEM')

        if self._config['FIRST_IDENTIFIER']['MODE'] == 'redeem':
            self._config['FIRST_IDENTIFIER']['REDEEM_ID'] = None
            if self._config['FIRST_IDENTIFIER']['REDEEM_ID'] is None:
                redeems = api.get_redeem_list(
                    self.tws.config['TWITCH_BOT'], 
                    self.tws.config['TWITCH_BOT']['BOT_NICK']
                )
                if len(redeems) == 0:
                    print('There are no redemptions. Skipping.')    
                else:
                    print('Here are the list of redemptions in the channel I am listening to:')
                    print(' ID : Title')
                    print(redeems)
                    while self._config['FIRST_IDENTIFIER']['REDEEM_ID'] not in redeems.keys():
                        self._config['FIRST_IDENTIFIER']['REDEEM_ID'] = input(
                            'Enter the ID next to the redemption title corresponding to your "first" redemption >'
                        )
                        if self._config['FIRST_IDENTIFIER']['REDEEM_ID'] not in redeems.keys():
                            print('Invalid input, your ID does not match any of the redemptions. Did you make a typo?')
                    self.tws.subscriptions += [
                        {
                            'event': 'channel.channel_points_custom_reward_redemption.add',
                            'version': '1',
                            'condition': {
                                'broadcaster_user_id': str(self.tws.user_id),
                                'reward_id': self._config['FIRST_IDENTIFIER']['REDEEM_ID'],
                            },
                        }
                    ]

        while self._config['FIRST_IDENTIFIER']['TEXT'] is None:
            self._config['FIRST_IDENTIFIER']['TEXT'] = input(
                '[FirstIdentifier] Which should say to congratulate the first chatter? (Use {chatter} where you would put the chatter name) >'
            )

        if 'BLACK_LIST' not in self._config['FIRST_IDENTIFIER']:
            self._config['FIRST_IDENTIFIER']['BLACK_LIST'] = []

        self._first_identifier_history_file = os.path.join(
            self._appdir.user_config_dir, 
            'redemption_history.json'
        )
        if not os.path.isfile(self._first_identifier_history_file):
            self._first_identifier_history = {
                x:{
                    'last_redeem': datetime.datetime(2000,1,1,0,0,0),
                    'score': {},
                }
                for x in self._channels
            }
            self.save_first_history()
        else:
            with open(self._first_identifier_history_file,'r') as f:
                self._first_identifier_history = json.load(f)
                for channel in self._first_identifier_history.keys():
                    self._first_identifier_history[channel]['last_redeem'] = datetime.datetime.strptime(self._first_identifier_history[channel]['last_redeem'], '%Y-%m-%d %H:%M:%S')
        self.save_config()

    def save_first_history(self):
        cfgs = copy.deepcopy(self._first_identifier_history.copy())
        for channel in cfgs.keys():
            cfgs[channel]['last_redeem'] = cfgs[channel]['last_redeem'].strftime('%Y-%m-%d %H:%M:%S')
        with open(self._first_identifier_history_file, 'w') as f:
            json.dump(
                cfgs,
                f
            )

    @restrict_message(default=True, live_only=False)
    async def event_message(self, message: Message):
        await super().event_message(message=message)
        if self._config['FIRST_IDENTIFIER']['MODE'] != 'chat':
            return
            
        is_live = self._is_live.get(message.channel.name) is not None
        if not is_live:
            return

        redeemed = self._first_identifier_history[message.channel.name]['last_redeem'] > self._is_live[message.channel.name]
        if redeemed:
            return

        if message.author.name.lower() in self._config['FIRST_IDENTIFIER']['BLACK_LIST']:
            return

        await self.recognise_first_chatter(message)

    async def recognise_first_chatter(self, message: Message):
        await message.channel.send(self._config['FIRST_IDENTIFIER']['TEXT'].format(chatter=message.author.name))
        if message.author.name not in self._first_identifier_history[message.channel.name]['score']:
            self._first_identifier_history[message.channel.name]['score'][message.author.name] = 1
        else:
            self._first_identifier_history[message.channel.name]['score'][message.author.name] += 1
        self._first_identifier_history[message.channel.name]
        self._first_identifier_history[message.channel.name]['last_redeem'] = datetime.datetime.now()
        self.save_first_history()
        await message.channel.send(self.user_first_score(message.channel.name, message.author.name))
        await message.channel.send(self.get_score_board(message.channel.name))

    def channel_channel_points_automatic_reward_redemption_add(self, message_dict):
        super().channel_channel_points_automatic_reward_redemption_add(message_dict)
        if message_dict['reward']['id'] == self._config['FIRST_IDENTIFIER']['REDEEM_ID']:
            asyncio.create_task(self.recognise_first_chatter(message_dict))

    async def recognise_first_redeemer(self, message_dict):
        target_channel = message_dict['broadcaster_user_name']
        redeemer = message_dict['user_name']
        channels = [x for x in self.connected_channels if x.name == target_channel]
        if len(channels) == 0:
            return
        else:
            channel = channels[0]
        await channel.send(self._config['FIRST_IDENTIFIER']['TEXT'].format(chatter=redeemer))
        if redeemer not in self._first_identifier_history[channel.name]['score']:
            self._first_identifier_history[channel.name]['score'][redeemer] = 1
        else:
            self._first_identifier_history[channel.name]['score'][redeemer] += 1
        self._first_identifier_history[channel.name]
        self._first_identifier_history[channel.name]['last_redeem'] = datetime.datetime.now()
        self.save_first_history()
        await channel.send(self.user_first_score(channel.name, redeemer))
        await channel.send(self.get_score_board(channel.name))

    def get_score_board(self, channel: str):
        score = self._first_identifier_history[channel]['score']
        rank = sorted(score.keys(), key=lambda x: -score[x])
        text = ''
        if len(rank) == 0:
            text = 'There is no one on the podium yet.'
            return None
        else:
            order = ['1st','2nd','3rd']
            text = ' | '.join(["Top 3 first chatters"] + [order[ii] + ' - ' + x + f' [{score[x]}]' for ii,x in enumerate(rank[:3])])
        return text

    @commands.command()
    async def first_me(self, ctx: commands.Context):
        await self.send(ctx, self.user_first_score(ctx.channel.name, ctx.author.name))

    def user_first_score(self, channel: str, user: str):
        score = self._first_identifier_history[channel]['score']
        rank_score = score[user]
        rank = sorted(score.keys(), key=lambda x: -score[x])
        if user in rank:
            rank_user = rank.index(user) + 1
            text = f"@{user} you've been first {rank_score} times. You're currently ranked {rank_user}."
        else:
            text = f"@{user} you haven't been a first chatter yet Sadge"
        return text

    @commands.command()
    async def first(self, ctx: commands.Context):
        await self.send(ctx, self.get_score_board(ctx.channel.name))