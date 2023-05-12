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
        self._cd: Optional[routines.Routine] = {channel:{} for channel in initial_channels}

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
        channel = ctx.channel.name
        if content[0] != '{}cd'.format(self._prefix):
            return
        elif not content[1].isnumeric():
            if len(content) == 2:
                key = None
            else:
                key = content[2]
            if content[1].lower() in ['stop','wait']:
                message = self.stop_countdown(channel, key=key)
                await ctx.send(message)
            else:
                await ctx.send(invalid_command_message)
        else:
            dt = int(content[1])
            if len(content) == 2:
                key = None
            else:
                key = content[2]
            if self.has_cd(channel, key):
                await ctx.send(self.stop_countdown(channel, key=key, new_dt=dt))
            else:
                await ctx.send('Countdown started! {}'.format(self.format_time_remain(dt, key)))
            self._cd[channel]['_base' if key is None else key] = asyncio.create_task(
                self.countdown_helper(
                    ctx, 
                    dt,
                    key=key,
                    )
            )
    
    def has_cd(self, channel, key):
        key = '_base' if key is None else key
        if key not in self._cd[channel]:
            output = False
        elif isinstance(self._cd[channel][key], asyncio.Task):
            output = True
        else:
            output = False
        return output

    def format_time_remain(self, mod_dt, key=None):
        if mod_dt <= 0:
            message = 'Go!'
        else:
            if mod_dt <= 60:
                message = str(mod_dt) + '...'
            elif mod_dt <= 60*5:
                s = str(mod_dt % 60)
                if len(s) == 1:
                    s = '0'+s
                message = str(math.floor(mod_dt/60)) + ':' + s + '...'
        if key is not None:
            message = key + ': ' + message
        return message
    
    async def countdown_helper(self, ctx: commands.Context, duration, key=None):
        await asyncio.sleep(1.1)
        start_time = time.time()
        end_time = start_time + duration
        last = self.format_time_remain(math.ceil(end_time - start_time), key=key)
        t = start_time
        while True:
            time_now = time.time()
            total_dt = end_time - time_now

            if total_dt <= 5:
                mod = 1
            elif total_dt <= 30:
                mod = 5
            elif total_dt <= 60:
                mod = 10
            elif total_dt <= 5*60:
                mod = 30
            elif total_dt <= 10*60:
                mod = 60
            dt = total_dt % mod
                
            mod_dt = int(math.ceil(total_dt/mod)*mod)
            int_dt = math.ceil(total_dt)
            message = self.format_time_remain(mod_dt, key=key)
            t_now = time.time()
            last_dt = t_now - t
            dt = max([1.05-last_dt, dt, 0]) #Make sure the next dt always gives about 1.05s between messages and is not negative

            if message != last and mod_dt==int_dt:
                last = message
                message = '{}'.format(message)
                #print('Print {}'.format(message))
                await ctx.send(message)
                t = t_now
                if (total_dt - dt) < 5:
                    end_time += 0.05
                    
            if total_dt <= 0:
                break

            await asyncio.sleep(dt)

        key = '_base' if key is None else key
        self._cd[ctx.channel.name][key] = None

    def stop_countdown(self, channel, key=None, new_dt=None):
        key = '_base' if key is None else key
        if isinstance(self._cd[channel][key], asyncio.Task):
            if new_dt:
                message = 'Countdown replaced! {}'.format(self.format_time_remain(new_dt, key))
            else:
                message = 'Countdown has been cancelled.'
            self._cd[channel][key].cancel()
            self._cd[channel][key] = None
        else:
            message = 'Some weird stuff happened: countdown reset.'
            self._cd[channel][key] = None
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