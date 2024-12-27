import os

from mountaineer_bot import _cfg_loc

if __name__ == "__main__":
    from appdirs import AppDirs
    appdir = AppDirs(appname='test', appauthor=_cfg_loc, roaming=True)
    print('The following profiles have been found:')
    for x in os.listdir(os.path.split(appdir.user_config_dir)[0]):
        if x.startswith('_') and 'backup' in x:
            continue
        print(f'{x} [{os.path.join(os.path.split(appdir.user_config_dir)[0], x)}]')