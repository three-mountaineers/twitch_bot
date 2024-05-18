import os

from twitchio.ext import commands

from mountaineer_bot import windows_auth, twitch_auth
from mountaineer_bot.security import restrict_command

class BotMixin:
    def __init__(self, config_file: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = windows_auth.get_password(windows_auth.read_config(config_file))
        self._config_dir = os.path.split(config_file)[0]
        self._required_scope = []
        self._repeat_preventer = '\U000e0000'

    async def send(self, ctx, message):
        await ctx.send(self.ck(message))
        return

    def parse_content(self, s):
        return s.strip(self._repeat_preventer).strip().replace(self._repeat_preventer, '').split()

class Bot(BotMixin, commands.Bot):
    def __init__(
        self,
        config_file: str,
        **kwargs
    ):
        _configs = windows_auth.get_password(windows_auth.read_config(config_file))
        super().__init__(
            config_file=config_file,
            token=twitch_auth.refresh_access_token(config=_configs, user=_configs['BOT_NICK']),
            prefix= _configs['BOT_PREFIX'],
            client_id = _configs['CLIENT_ID'], 
            client_secret = _configs['SECRET'],
            initial_channels = _configs['CHANNELS'],
            nick = _configs['BOT_NICK'], 
            loop = None,
            heartbeat = 30,
            retain_cache = True,
            **kwargs
            )
        self._required_scope += [
            'chat:read',
            'chat:edit',
            ]
        self._http._refresh_token = windows_auth.get_refresh_token(config=self._config, username=_configs['BOT_NICK'])
        self._user = _configs['BOT_NICK']
        self._invalid_response = self._config['INVALID_COMMAND_RESPONSE']
        self._no_permission_response = self._config['NO_PERMISSION_RESPONSE']
        self._bot_whitelist = self._config.get('WHITE_LIST_USERS',[])
        self._repeat_preventer = '\U000e0000'
        self._last_message = '' 

    def run(self):
        print('Running in channels: {}'.format(', '.join(self._config['CHANNELS'])))
        print('Starting bot...')
        super().run()
        print('Ready')

    def ck(self, message):
        if self._last_message == message:
            self._last_message = message + self._repeat_preventer
            return message + self._repeat_preventer
        self._last_message = message
        return message

    async def event_ready(self):
        print(f"{self.nick} is online!")

    @commands.command()
    async def where(self, ctx: commands.Context):
         await self.send(ctx, f'Hello, I am here!')

    @commands.command()
    async def hello(self, ctx: commands.Context):
        await self.send(ctx, f'Hello {ctx.author.name}!')

    @commands.command()
    @restrict_command(['Mods', 'Broadcaster'])
    async def add_whitelist(self, ctx: commands.Context):
        content = self.parse_content(ctx.message.content)
        if content[1] not in self._bot_whitelist:
            await self.send(ctx, f"You're cool {content[1]}")
            self._bot_whitelist.append(content[1])
        else:
            await self.send(ctx, f"{content[1]} is already cool with me!")

    @commands.command()
    @restrict_command(['Mods', 'Broadcaster'])
    async def remove_whitelist(self, ctx: commands.Context):
        content = self.parse_content(ctx.message.content)
        if content[1] not in self._bot_whitelist:
            await self.send(ctx, f"I wasn't cool with you anyway {content[1]}")
        else:
            await self.send(ctx, f"You're dead to me {content[1]}!")
            self._bot_whitelist.remove(content[1])