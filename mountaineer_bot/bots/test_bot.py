import time
from mountaineer_bot.components import FirstIdentifier

from mountaineer_bot.core import Bot
from mountaineer_bot.entry_point import main

from mountaineer_bot import windows_auth, twitch_auth
from mountaineer_bot.core import Bot
from mountaineer_bot.twitch_auth import main as grant_scope_main

class CustomBot(FirstIdentifier, Bot):
    pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config_file', type=str)
    args = vars(parser.parse_args())
    configs = windows_auth.get_password(windows_auth.read_config(args['config_file']))
    bot = CustomBot(**args)
    scopes = bot._required_scope
    grant_scope_main(config=args['config_file'], scopes=scopes)
    if 'refresh_token' not in configs:
        bot = CustomBot(**args)

    @bot.event
    async def event_channel_point_custom_reward_redemption(channel, reward):
        # Extract relevant data from the event
        user = reward.user.display_name
        reward_title = reward.title
        message = f'{user} redeemed {reward_title}'

        # Implement your desired logic here (e.g., respond to the redemption)
        # For demonstration purposes, we'll print the redemption message
        logging.log(logging.INFO, message)

    bot.run()