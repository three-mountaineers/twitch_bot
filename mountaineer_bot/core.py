from typing import Union, Callable, Optional, Dict

import time
import asyncio
import math

from twitchio.ext import commands, routines

from mountaineer_bot import windows_auth, twitch_auth

class Bot(commands.Bot):
    def __init__(
        self,
        token: str,
        configs: Dict[str, str],
        *,
        client_secret: str = None,
        initial_channels: Union[list, tuple, Callable] = None,
        loop: asyncio.AbstractEventLoop = None,
        heartbeat: Optional[float] = 30.0,
        retain_cache: Optional[bool] = True,
        refresh_token: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            token=token,
            client_secret = client_secret,
            initial_channels = initial_channels,
            loop = loop,
            heartbeat = heartbeat,
            retain_cache = retain_cache,
            **kwargs
            )
        self._http._refresh_token = refresh_token
        self._configs = configs
        self._cd: Optional[routines.Routine] = None

    async def event_ready(self):
        print(f"{self._configs['BOT_NICK']} is online!")

    @commands.command()
    async def where(self, ctx: commands.Context):
         await ctx.send(f'Hello, I am here!')

    @commands.command()
    async def hello(self, ctx: commands.Context):
         await ctx.send(f'Hello {ctx.author.name}!')

    @commands.command()
    async def cd(self, ctx: commands.Context):
        invalid_command_message = 'Invalid command for !cd'
        content = ctx.message.content.split(' ')
        if content[0] != '!cd':
            return
        elif not content[1].isnumeric():
            if content[1] == 'stop':
                message = self.stop_countdown()
                await ctx.send(message)
            else:
                await ctx.send(invalid_command_message)
        else:
            if isinstance(self._cd, asyncio.Task):
                await ctx.send('Countdown cancelled.')
                self._cd.cancel()
                self._cd = None
            self._cd = asyncio.create_task(self.countdown_helper(ctx, int(content[1])))
            await ctx.send(f'Countdown started!')
    
    async def countdown_helper(self, ctx: commands.Context, duration):
        start_time = time.time()
        end_time = start_time + duration
        last = ''
        while True:
            time_now = time.time()
            total_dt = int(math.ceil(end_time - time_now))

            if total_dt <= 5:
                dt = 1
                mod = 1
            elif total_dt <= 30:
                mod = 5
                dt = min([total_dt-5, mod])
            elif total_dt <= 60:
                mod = 10
                dt = min([total_dt-30, mod])
            elif total_dt <= 5*60:
                mod = 30
                dt = min([total_dt-60, mod])
            elif total_dt <= 10*60:
                mod = 60
                dt = min([total_dt-2*60, mod])
            dt = float(dt)/2

            mod_dt = int(math.ceil(total_dt/mod)*mod)
            if total_dt <= 0:
                message = 'Go!'
            else:
                if mod_dt <= 60:
                    message = str(mod_dt) + '...'
                elif mod_dt <= 60*5:
                    s = str(mod_dt % 60)
                    if len(s) == 1:
                        s = '0'+s
                    message = str(math.floor(mod_dt/60)) + ':' + s + '...'
            
            if message != last:
                last = message
                message = '{}'.format(message)
                await ctx.send(message)

            if total_dt <= 0:
                break

            await asyncio.sleep(dt)
        self._cd = None

    def stop_countdown(self):
        if (not hasattr(self, '_cd')) or self._cd is None:
            message = 'No countdown is active.'
        elif isinstance(self._cd, asyncio.Task):
            message = 'Countdown has been cancelled.'
            self._cd.cancel()
            self._cd = None
        else:
            message = 'Some weird stuff happened: countdown reset.'
            self._cd = None
        return message

def create_bot(config, user):
    access_token = twitch_auth.refresh_access_token(config=config, user=user)
    refresh_token = windows_auth.get_refresh_token(config=config, username=user)
    bot = Bot(
        token=access_token, 
        configs=config,
        client_id=config['CLIENT_ID'], 
        client_secret=config['SECRET'], 
        nick=config['BOT_NICK'], 
        prefix=config['BOT_PREFIX'], 
        initial_channels=config['CHANNELS'],
        refresh_token=refresh_token,
        )
    return bot