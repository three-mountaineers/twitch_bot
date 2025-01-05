import random
import os
import time
import sys

from appdirs import AppDirs

import mountaineer_bot as mtb
from mountaineer_bot import windows_auth, twitch_auth
from mountaineer_bot.twitchauth import device_flow

class SpinningCursor:
    def spinning_cursor(self):
        while True:
            for cursor in '|/-\\':
                yield cursor

    def spin(self, t: int):
        spinner = self.spinning_cursor()
        for _ in range(t*4):
            sys.stdout.write(next(spinner))
            sys.stdout.flush()
            time.sleep(0.25)
            sys.stdout.write('\b')

    def terminal_pause(self, t: int=2):
        print('')
        print('')
        self.spin(t)

def main(pause_time: int=1, headless:bool=True):
    spinner = SpinningCursor()
    print('============================================================================================')
    print('....*.*...*.......*..*.......*....*..*.........*..........*.....*..*............*.....*.....')
    print('..*......*....*.......*..*...... MOUNTAINEERS BOT SETUP .....*.....*..*.......*.....*.......')
    print('...*.*.....*....*.........*..*..*..*..*.......*......*.................*.*.*...*.........*..')
    print('============================================================================================')
    spinner.terminal_pause(0)
    print('Welcome to the mountaineers bot - this setup process will assist you with the setup process.')
    spinner.terminal_pause(pause_time)
    bot_profile = input('What name do you want to give this new bot profile (no spaces allowed)? > ')
    spinner.terminal_pause(pause_time)
    appdir = AppDirs(appname=bot_profile, appauthor=mtb._cfg_loc, roaming=True)
    profile_exists = os.path.isfile(os.path.join(appdir.user_config_dir, 'env.cfg'))
    if profile_exists:
        overwrite = input('The profile already exists. Do you want to overwrite it? (Y/N) > ').lower()
        while overwrite not in ('y','n'):
            overwrite = input('Please enter either Y or N. (Y/N) ').lower()
        spinner.terminal_pause(pause_time)
    else:
        overwrite = 'y'
    if overwrite == 'n':
        print("Existing profile kept. Attempting to authenticate.")
        device_flow.initial_authenticate(
            os.path.join(appdir.user_config_dir, 'env.cfg'),
            scopes=[twitch_auth.TWITCH_SCOPES['read_chat']],
            headless=headless,
        )
        print('Setup complete. Exiting...')
        spinner.terminal_pause(pause_time)
        return
    elif profile_exists:
        backup_profile = '_' + bot_profile + '_backup_' + ("%032x" % random.getrandbits(128))[:4]
        appdir_old = AppDirs(appname=backup_profile, appauthor=mtb._cfg_loc, roaming=True)
        os.makedirs(appdir_old.user_config_dir)
        for x in os.listdir(appdir.user_config_dir):
            os.rename(
                os.path.join(appdir.user_config_dir, x), 
                os.path.join(appdir_old.user_config_dir, x)
            )
        print(f"Old profile has been saved in location {appdir_old.user_config_dir}")
        spinner.terminal_pause(pause_time)
    else:
        if not os.path.isdir(appdir.user_config_dir):
            os.makedirs(appdir.user_config_dir)
    env_template = {
        "PORT": '3000',
        'BOT_PREFIX': '',
        'CHANNELS': [],
        'WHITE_LIST_USERS': [],
        'BLACK_LIST_USERS': [],
    }

    env_template['WIN_CRED_KEY'] = ("%032x" % random.getrandbits(128))

    print("We are now going to set up your profile.")
    spinner.terminal_pause(pause_time)
    print("1. Go to: https://dev.twitch.tv/console (make sure you are logged in as the bot user account)")
    print('2. Click on "Register your Application"')
    print("3. Create a name. Note this down")
    print("4. OAuth Redirect URL: type `http://localhost:3000`. If it won't let you, set it to `http://localhost`.")
    print("5. Category: Chat Bot")
    print("6. Client Type: Confidential")
    print("7. Create")
    print("8. In the next screen, click on \"Manage\" in the new row that's been created")
    print("9. If step 4 didn't work, change the OAuth Redirect URL now.")
    check = ""
    while check != "y":
        client_id = input('10: Please enter the "Client ID" that has been shown > ')
        env_template['CLIENT_ID'] = client_id
        spinner.terminal_pause(pause_time)
        print(f'You have entered: {client_id}')
        spinner.terminal_pause(pause_time)
        check = input("Please confirm that this is correct (Y/N) > ").lower()
        while check not in ("n","y"):
            check = input("Invalid input. Please confirm the client_id is correct (Y/N) > ").lower()
    spinner.terminal_pause(pause_time)
    check = ""
    while check != "y":
        client_secret = input('11: Click on the \"New Secret\" button. Please enter the the generated text here > ')
        spinner.terminal_pause(pause_time)
        print(f'You have entered: {client_secret}')
        spinner.terminal_pause(pause_time)
        check = input("Please confirm that this is correct (Y/N) > ").lower()
        while check not in ("n","y"):
            check = input("Invalid input. Please confirm the client_secret is correct (Y/N) > ").lower()
    spinner.terminal_pause(pause_time)
    print('Connecting the profile to your twitch account. Please make sure you are logged into the the right account when you click `Activate` in the window that will popup.')
    spinner.terminal_pause(pause_time)
    env_template['BOT_NICK'] = device_flow.initial_authenticate(
        config=env_template,
        scopes=[twitch_auth.TWITCH_SCOPES['read_chat']],
        headless=headless,
    )
    spinner.terminal_pause(pause_time)
    print(f"Bot connected to twitch account: `{env_template['BOT_NICK']}`. If this is not correct, press `CTRL + C` to quit and start again.")
    spinner.terminal_pause(pause_time)
    while env_template['BOT_PREFIX'] == '':
        env_template['BOT_PREFIX'] = input('Please enter the command prefix the bot will recognise (suggest `!`) > ')
        spinner.terminal_pause(pause_time)
        if len(env_template['BOT_PREFIX']) != 1:
            print(f"Invalid input `{env_template['BOT_PREFIX']}`. Prefix must be a single character.")
            spinner.terminal_pause(pause_time)

    while len(env_template['CHANNELS']) == 0:
        env_template['CHANNELS'] = '\n'.join([x.strip() for x in input('Please enter the channels the bot will run on. Separate each channel with a `;` > ').split(';')])
        spinner.terminal_pause(pause_time)
        if len(env_template['CHANNELS']) == 0:
            print(f"Invalid input. At least one channel must be specified.")
            spinner.terminal_pause(pause_time)
    print('Entered channels for bot to run on are:')
    print(env_template['CHANNELS'])
    spinner.terminal_pause(pause_time)
    env_template['INVALID_COMMAND_RESPONSE'] = input('Please enter what the bot will say if someone uses an invalid command > ')
    spinner.terminal_pause(0)
    print(f"What the bot will say if there\'s any invalid command: {env_template['INVALID_COMMAND_RESPONSE']}")
    spinner.terminal_pause(pause_time)
    env_template['NO_PERMISSION_RESPONSE'] = input('Please enter what the bot will say if someone uses a command they\'re not allowed to > ')
    spinner.terminal_pause(0)
    print(f"What the bot will say if a person tries to use a command they\'re not allowed to use: {env_template['NO_PERMISSION_RESPONSE']}")
    spinner.terminal_pause(pause_time)

    print(f'Completing setup...')
    spinner.terminal_pause(pause_time)
    windows_auth.set_password(env_template, secret=client_secret)

    windows_auth.write_config(
        cfg_location=os.path.join(appdir.user_config_dir, 'env.cfg'),
        val=env_template,
        key='TWITCH_BOT',
    )

    spinner.terminal_pause(pause_time)

    print(f'Setup complete. The configurations are stored in: {os.path.join(appdir.user_config_dir, "env.cfg")} ')
    print("If any settings need to be updated, you will be able to edit it from that file.")
    print("Exiting setup...")
    spinner.spin(2)
    return

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--headless', action='store_true')
    kwargs = vars(parser.parse_args())
    main(**kwargs)