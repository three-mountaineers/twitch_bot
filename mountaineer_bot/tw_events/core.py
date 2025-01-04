from typing import Literal, Any, Type, Callable, Awaitable

import json
import requests
import os
import logging
import appdirs

from typing import TypedDict

from appdirs import AppDirs
import rel
import asyncio

import mountaineer_bot as mtb
from mountaineer_bot.core import Bot
from mountaineer_bot.tw_events.scopes import REQUIRED_SCOPE
from mountaineer_bot import windows_auth, api, api
from mountaineer_bot.twitchauth import core as twitch_auth, device_flow
import mountaineer_bot as mbt

class Subscription(TypedDict):
    event: str
    version: int
    condition: dict

class ListenerMixin:
    _cfg = ''
    user_id = 0
    def __init__(self, *args, **kwargs):
        self.configs = os.path.join(self._config_dir, 'events_config.yml')

    def add_subscriptions(self, subscriptions: list[Subscription]):
        if not hasattr(self, 'subscriptions'):
            self.subscriptions: list[Subscription] = subscriptions
        else:
            self.subscriptions += subscriptions

import websockets

class BotEventMixin:
    tws: "TwitchWebSocket"
    pass

def pass_message(cls,  message_dict):
    pass

for scope in REQUIRED_SCOPE.keys():
    setattr(BotEventMixin, scope.replace('.','_'), pass_message)

class TwitchWebSocket:
    def __init__(
        self, 
        profile: str,
        bot: BotEventMixin,
        *args,
        **kwargs,
    ):
        appdir = appdirs.AppDirs(
            appname=profile,
            appauthor=mtb._cfg_loc,
            roaming=True,
        )
        self.config = windows_auth.read_config(os.path.join(appdir.user_config_dir, 'env.cfg'), key=None)
        windows_auth.get_password(self.config['TWITCH_BOT'])
        self.subscriptions: list[Subscription] = []
        self.subscribed_events: dict[
            str, 
            Callable
        ] = []
        self.get_user_info()
        super().__init__(*args, **kwargs)
        self.granted_scopes = twitch_auth.refresh_token(self.config['TWITCH_BOT'])
        self._transport = {}
        self.session_id = None
        self.bot = bot
        bot.tws = self
        self.add_scopes()

    async def start(self, reconnect: bool=True):
        while True:
            async with websockets.connect(
                'wss://eventsub.wss.twitch.tv/ws',
            ) as websocket:
                while True:
                    try:
                        websocket.state
                        message = await websocket.recv()
                        await self.on_message(message)
                    except websockets.ConnectionClosed as e:
                        print(e.args[0])
                        if reconnect:
                            logging.info('Websocket reconnecting')
                        else:
                            logging.info('Websocket disconnected.')
                        break
                if not reconnect:
                    break

    def add_scopes(self):
        scopes = list(set([
            y
            for x in self.subscriptions
            for y in REQUIRED_SCOPE[x['event']]
            if y is not None
        ]))
        if any([x for x in scopes if x not in self.granted_scopes]):
            device_flow.initial_authenticate(
                self.config['TWITCH_BOT'],
                scopes=list(set(self.granted_scopes + scopes)),
                headless=False,
            )
            self.granted_scopes = twitch_auth.refresh_token(self.config['TWITCH_BOT'])

    async def on_message(self, message: Any):
        message_dict = json.loads(message)
        message_switch = self._message_switch(message_dict)
        if message_switch == "session_welcome":
            self.session_welcome(message_dict)
        else:
            if hasattr(self.bot, message_switch):
                getattr(self.bot, message_switch)(message_dict)
            else:
                logging.debug(f"Message [{message_switch}]: {message}")

    def session_welcome(self, message: dict):
        logging.debug(f"Message type - session_welcome")
        self.session_id = message['payload']['session']['id']
        self._transport = {
            'method': 'websocket',
            'session_id': self.session_id,
        }

    def _message_switch(self, message: dict):
        if message["metadata"]["message_type"] == "session_welcome":
            return "session_welcome"
        elif message["metadata"]["message_type"] == "session_keepalive":
            return "session_keepalive"
        elif message["metadata"]["message_type"] == "notification":
            return message["metadata"]["subscription_type"].replace('.','_')
        
    def subscribe_to_event(self, subscription: Subscription):
        assert subscription['event'] in REQUIRED_SCOPE.keys(), f"{subscription['event']} is not one of available topics."
        access_token = windows_auth.get_access_token(self.config['TWITCH_BOT'], self.config['TWITCH_BOT']['CLIENT_ID'])

        data = {
            'type': subscription['event'],
            'version': str(subscription['version']),
            'condition': subscription['condition'],
            'transport': self._transport
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Client-Id": self.config['TWITCH_BOT']['CLIENT_ID'],
            "Content-Type": "application/json",
        }
        r = requests.post(
            url = "https://api.twitch.tv/helix/eventsub/subscriptions",
            data = json.dumps(data),
            headers = headers,
        )
        
        if r.status_code >= 400:
            logging.error(f'subscribing to {subscription['event']} failed: {r.content}')
        else:
            logging.info(f'subscribed to {subscription['event']} response [{r.status_code}]')

    def get_user_info(self):
        logging.debug('getting user info')
        self.user_id = api.get_user_id(self.config['TWITCH_BOT'], self.config['TWITCH_BOT']['BOT_NICK'])

async def main(listener: Type[TwitchWebSocket], profile: str, logging_level: int, **kwargs):
    logging.getLogger().setLevel(logging_level)
    tws = listener(profile=profile, **kwargs)
    await tws.start()

if __name__ == "__main__":
    asyncio.run(
        main(
            listener = TwitchWebSocket,
            profile = 'three_mountaineers',
            logging_level = logging.DEBUG,
        )
    )