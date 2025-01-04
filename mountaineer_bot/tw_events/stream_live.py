import os
from appdirs import AppDirs
import yaml

from mountaineer_bot.tw_events.core import Subscription, ListenerMixin
from mountaineer_bot import api

class StreamStatusMixin(ListenerMixin):
    """
    This only works for your own channel.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        
        if not os.path.isfile(self._sound_reactor_config_file):
            pass

        if 'subscribed_channels' not in kwargs:
            return

        broadcaster_ids = [
            api.get_user_id(self.config['TWITCH_BOT'], x)
            for x in kwargs['subscribed_channels']
        ]        

        stream_live: list[Subscription] = [
            {
                'event': 'stream.online',
                'condition': {
                    'broadcaster_user_id': x
                },
                'version': 1,
            }
            for x in broadcaster_ids
        ]

        stream_down: list[Subscription] = [
            {
                'event': 'stream.offline',
                'condition': {
                    'broadcaster_user_id': x
                },
                'version': 1,
            }
            for x in broadcaster_ids
        ]

        self.add_subscriptions(stream_down + stream_live)

    def load_config(self):
        with open(self._sound_reactor_config_file,'r') as f:
            self.sound_reactor_config = yaml.load(f, Loader=yaml.SafeLoader)

    def stream_live(self, func):
        self.subscribed_events['stream_live'].append(func)
        return func

    def stream_offline(self, func):
        self.subscribed_events['stream_offline'].append(func)
        return func
        
        
