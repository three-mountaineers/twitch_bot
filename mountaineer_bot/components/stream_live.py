import datetime

from twitchio.ext import commands

from mountaineer_bot import BotMixin, BotEventMixin
from mountaineer_bot.security import restrict_command
from mountaineer_bot import api

times = [
    (60, 'seconds'),
    (60, 'minutes'),
    (24, 'hours'),
    (365, 'days'),
]

class StreamLiveEventListener(BotEventMixin):
    def __init__(self, *args, **kwargs):
        self.add_required_scope([
            'chat:edit',
        ])
        super().__init__(*args, **kwargs)
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
        self.initial_is_live()

    def initial_is_live(self):
        for channel in self._channels:
            self._is_live[channel] = api.get_user_live(self._config['TWITCH_BOT'], channel)

    def stream_online(self, message_dict, version):
        self._is_live[message_dict['broadcaster_user_name']] = datetime.datetime.now()
        super().stream_online(message_dict, version)

    def stream_offline(self, message_dict, version):
        self._is_live[message_dict['broadcaster_user_name']] = None
        super().stream_offline(message_dict, version)

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        if ctx.channel.name not in self._is_live:
            return
        time = self._is_live[ctx.channel.name]
        if time is None:
            await self.send(ctx.channel.name, message=f'{ctx.channel.name} is not live.')
        else:
            uptime = (datetime.datetime.now() - time).total_seconds()
            strs = []
            for time_denom, time_str in times:
                strs.append(str(uptime % time_denom)  + ' ' + time_str)
                uptime = uptime // time_denom
            uptime_str = ' '.join(strs[::-1])
            await self.send(ctx.channel.name, message=f'{ctx.channel.name} has been live for {uptime_str}')