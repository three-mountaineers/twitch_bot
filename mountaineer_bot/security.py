from typing import Literal, List

from functools import wraps

def restrict_command(
        allowed: List[Literal['Whitelist', 'Broadcaster', 'Mods']]=['Broadcaster'], 
        default=False, 
        blacklist_enabled=True
    ):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            if 'Broadcaster' in allowed and ctx.author.is_broadcaster:
                is_allowed = True
            elif blacklist_enabled and ctx.author.name in self._bot_blacklist:
                is_allowed = False
            elif 'Mods' in allowed and ctx.author.is_mod:
                is_allowed = True
            elif 'Whitelist' in allowed and ctx.author.name in self._bot_whitelist:
                is_allowed = True
            else:
                is_allowed = default
            if not is_allowed:
                await self.send(ctx, self._no_permission_response)
            else:
                await func(self, ctx, *args, **kwargs)
        return wrapper
    return decorator