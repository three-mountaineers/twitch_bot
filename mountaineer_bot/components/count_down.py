from typing import Dict, Optional
import asyncio
import math
import time

from twitchio.ext import commands, routines

from mountaineer_bot import BotMixin
from mountaineer_bot.security import restrict_command
from mountaineer_bot.utils import to_float

class CountdownMixin(BotMixin):
    _required_scope = [
        'chat:read',
        'chat:edit',
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cd: Dict[str, Dict[str, Optional[routines.Routine]]] = {channel:{} for channel in self._config['CHANNELS']}
        
        self._countdown_go_text = self._config.get('COUNTDOWN_GO_TEXT',[])

    @commands.command()
    @restrict_command(['Mods', 'Broadcaster','Whitelist'])
    async def cd(self, ctx: commands.Context):
        content = self.parse_content(ctx.message.content)
        channel = ctx.channel.name
        dt = to_float(content[1])
        
        if dt is None:
            if len(content) == 2:
                key = None
            else:
                key = content[2]
            if content[1].lower() in ['stop','wait']:
                message = self.stop_countdown(channel, key=key)
                await self.send(ctx, message)
            else:
                if self._invalid_response is not None:
                    await self.send(ctx, self._invalid_response)
        elif dt <= 0:
            if self._invalid_response is not None:
                await self.send(ctx, self._invalid_response)
        else:
            if len(content) == 2:
                key = None
            else:
                key = content[2]
            if self.has_cd(channel, key):
                await self.send(ctx, "I'm already counting down!")
                return
            else:
                await self.send(ctx, 'Countdown starting...')
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
            message = self._countdown_go_text
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
        end_time = start_time + round(duration)
        while True:
            time_now = time.time()
            total_dt = end_time - time_now
            int_dt = round(total_dt)

            # Print the time
            message = self.format_time_remain(int_dt, key=key)
            await self.send(ctx, message)
            #print(message)
            if message == self.format_time_remain(0):
                break

            # Work out the next time
            if round(total_dt) <= 5:
                mod = 1
            elif round(total_dt) <= 30:
                mod = 5
            elif round(total_dt) <= 60:
                mod = 10
            elif round(total_dt) <= 5*60:
                mod = 30
            elif round(total_dt) <= 10*60:
                mod = 60
            dt = total_dt % mod

            if (total_dt - dt) == int_dt:
                dt = mod
                
            adj_dt = max([1.05, dt, 0]) #Make sure the next dt always gives about 1.05s between messages and is not negative

            if adj_dt > dt:
                total_dt = total_dt + (adj_dt - dt)
                dt = adj_dt

            # Wait for the required amount of time
            await asyncio.sleep(dt)

        key = '_base' if key is None else key
        self._cd[ctx.channel.name][key] = None

    def stop_countdown(self, channel, key=None):
        key = '_base' if key is None else key
        if key not in self._cd[channel].keys() or self._cd[channel][key] is None:
            message = "There's no active countdown."
        elif isinstance(self._cd[channel][key], asyncio.Task):
            message = 'Countdown has been cancelled.'
            self._cd[channel][key].cancel()
            self._cd[channel][key] = None
        else:
            message = 'Some weird stuff happened: countdown reset.'
            self._cd[channel][key] = None
        return message
