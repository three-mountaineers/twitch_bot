# Change Log for Mountaineer Bot

This project adheres to [Semantic Versioning](https://semver.org)

## [0.1.2]
- Fixed text command looping to correctly detect when stream starts and trigger text command loops correctly (either going live after bot starts or vice versa)
- Changed uptime command to show integer numbers
- Change SoundReactor to require "chat:edit" permission so !sounds command can be used and responded to. Removed !sounds_refresh from returning a message.

## [0.1.1]
- Bug fix of NotRequired type hinting incompatible to older versions of python.

## [0.1.0]
- Official launch of event monitoring using websocket and integration to chat bot.
- Added auto detection of first chatter in the stream

## [0.0.3]
- Fixed for python version 3.10.

## [0.0.2] - YANKED
- Fixed setup and initial bot launch

## [0.0.1]
- Initial release

