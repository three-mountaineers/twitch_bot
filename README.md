# twitch_bot

## Installation

`mountaineer-bot` can be installed from pip using:

`pip install mountaineer-bot`

## Setting up a profile

Setup a profile using: `python -m mountaineer_bot.setup`. This will run you through a guided setup process. Artefacts that are generated as part of the bot's operation will be saved in the location shown at the end of the setup process.

Note this setup process will need to be done in interactive mode, so if you want to run this on a server, you will need to login to the server in the first instance to get it set up.

## Checking bot profiles that have been set up

Enter `python -m mountaineer_bot.list_profile` to see what profiles have been setup and available for use.

## Running a bot.

A bot can the run using the following command in command prompt: `python -m mountaineer_bot.bots.{bot_name} --profile {profile} --headless`. `{bot_name}` can be one of the following:"

* mod_bot: has the following features
    * Text Command
    * Count Down
    * Level Queue (one level per user in queue)
    * Scheduling
* mountaineer_bot: has the following features (build for ThreeMountaineers)
    * Text Command
    * Count Down
    * Level Queue (one level per user in queue)
    * Scheduling
* novae_bot: has the following features (build for NovaeStorm)
    * Text Command
    * Count Down
    * Level Queue (one level per user in queue)
    * Scheduling
* add_bot: has the following features
    * Identifies the first chatter in a stream and records it [experimental]

The `--profile` command will require a profile name setup from earlier in the setup step. The `--headless` command is only required if you're running this on a server in non-interactive mode.

## Acknowledgement

I wrote this code from scratch with the twichio framework. While I'll happy to share this code, please acknowledge my contribution by linking to [twitch.tv/three_mountaineers](https://www.twitch.tv/three_mountaineers)