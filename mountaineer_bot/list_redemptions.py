from appdirs import AppDirs

from mountaineer_bot import api, _cfg_loc, windows_auth


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--profile', type=str)

    args = vars(parser.parse_args())
    
    appdir = AppDirs(appname=args['profile'], appauthor=_cfg_loc, roaming=True)
    cfg = windows_auth.read_profile_config(profile=args['profile'])
    windows_auth.get_password(cfg['TWITCH_BOT'])

    print(f"Redemptions in channel: {cfg['TWITCH_BOT']['BOT_NICK']}")
    print(api.get_redeem_list(cfg['TWITCH_BOT'],  username=cfg['TWITCH_BOT']['BOT_NICK']))