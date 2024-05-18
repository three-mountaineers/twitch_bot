from twitchio.ext import commands
import time

from mountaineer_bot.core import Bot, BotMixin
from mountaineer_bot.entry_point import main

class FirstAdderMixin(BotMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sent = False
        self._required_scope = ['chat:read','chat:edit']

    @commands.command()
    async def open(self, ctx: commands.Context):
        channel = ctx.channel.name
        if channel in ['aurateur','three_mountaineers']:
            if not self.sent:
                await ctx.send(self._config['OPEN_REPLY'])
            self.sent = True
            
    @commands.command()
    async def queue(self, ctx: commands.Context):
        channel = ctx.channel.name
        if channel in ['aurateur','three_mountaineers']:
            print("I saw this in aura's channel")

class CustomBot(FirstAdderMixin, Bot):
    pass

if __name__ == "__main__":
    main(CustomBot)