import os
from appdirs import AppDirs

from mountaineer_bot.tw_events.core import Subscription, ListenerMixin

class PredictionMixin(ListenerMixin):
    """
    This only works for your own channel.
    """
    def __init__(self: "PredictionMixin", *args, **kwargs):
        super().__init__(*args, **kwargs)

        subscriptions: list[Subscription] = [
            {
                'event': 'channel.prediction.begin',
                'condition': {
                    'broadcaster_user_id': self.user_id
                },
                'version': 1,
            },
            {
                'event': 'channel.prediction.progress',
                'condition': {
                    'broadcaster_user_id': self.user_id
                },
                'version': 1,
            },
            {
                'event': 'channel.prediction.lock',
                'condition': {
                    'broadcaster_user_id': self.user_id
                },
                'version': 1,
            },
            {
                'event': 'channel.prediction.end',
                'condition': {
                    'broadcaster_user_id': self.user_id
                },
                'version': 1,
            }
        ]

        self.add_subscriptions(subscriptions)
        
        
        
