from mountaineer_bot.core import BotMixin

import os

_module_path_ = os.path.split(os.path.abspath(__file__))[0]
_cfg_loc = 'mountaineer_twitchbot_app'
if os.path.isfile(os.path.join(_module_path_, "version.py")):
    from mountaineer_bot.version import version as __version__, short_version, release
else:
    import warnings
    warnings.warn(
        'This package has been imported from source and not an installed version.',
        category=ImportWarning,
    )
    __version__ = '0.0.0.dev'
    del warnings


del os