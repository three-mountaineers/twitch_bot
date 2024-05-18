from typing import Literal, List

from functools import wraps

def restrict_command(allowed: List[Literal['Whitelist', 'Broadcaster', 'Mods', 'All']]):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            is_allowed = False
            if 'All' in allowed:
                is_allowed = True
            if 'Whitelist' in allowed and ctx.author.name in self._bot_whitelist:
                is_allowed = True or is_allowed
            if 'Broadcaster' in allowed and ctx.author.is_broadcaster:
                is_allowed = True or is_allowed
            if 'Mods' in allowed and ctx.author.is_mod:
                is_allowed = True or is_allowed
            if not is_allowed:
                await self.send(ctx, self._no_permission_response)
            else:
                await func(self, ctx, *args, **kwargs)
        return wrapper
    return decorator