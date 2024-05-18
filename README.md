# twitch_bot

## Section 1: Initial Setup

This is to set up all of the codes the bot needs.

1. Download python: https://www.python.org/downloads/release/python-31011/
2. Clone/Download this code
3. Hit "Windows key" + "Q" -> "Command Prompt"
4. Change directory to where you downloaded the code
5. Type the following into the "Command Prompt" window: `pip install -r requirements.txt`

## Section 2: Setting up Twitch Settings

We need to make an "application" for the bot to act as, and you'll allowing the bot to act on your behalf.

1. Go to: https://dev.twitch.tv/console
2. Click on "Register your Application"
3. Create a name. Note this down
4. OAuth Redirect URL: type `http://localhost:3000`. If it won't let you, set it to `http://localhost`.
5. Category: Chat Bot
6. Client Type: Confidential
7. Create
8. In the next screen, click on "Manage" in the new row that's been created
9. If step 4 didn't work, change the OAuth Redirect URL now.
10. Copy the "Client ID". Copy this somewhere.
11. Click on the "New Secret" button. Copy this somewhere AND DO NOT SHARE IT.

## Section 3: Configure the chatbot

We are going to populate the information the bot needs to talk Twitch now in the `env.cfg` file.

1. Line 2 - WIN_CRED_KEY: After the "=" you put anything you want (no spaces). This is what name we'll store all the sensitive information in the Windows Credential Store.
2. Line 3 - CLIENT_ID: After the "=", copy in the Client ID from step 9 in the last section.
3. Line 5 - BOT_NICK: The username of the account the bot will act as
4. Line 6 - CHANNELS: All of the channels you want this bot to participate in. Put each channel in a new line.
5. Hit "Ctrl + Windows key" -> "Credential Manager"
6. Hit the "Windows Credentials" tile
7. Under "Generic Credentials" hit "Add a generic credential"
8. Internet or network address, enter what you put in step 1 (everything after the "=" with no spaces)
9. User name: The "Client ID" you wrote down
10. Password: The "New Secret" you wrote down

## Section 4: Start the chatbot

1. Hit "Windows+ "Q" key -> "Command Prompt"
2. Change directory to where you downloaded the code
3. Type the following into the "Command Prompt" window: `python -m mountaineer_bot.bots.mod_bot -c env.cfg`
4. An authorization page might come up. Check the permissions needed and authorize if ok.
5. You should see "Running in channels: {channels you listed}", then "Starting bot..." and then "{your username} is online!". If you see these, congrats, the bot is ready to go! Otherwise, you might've gone down the Section 4 path.
6. When you're finished, close the window you created in this section.

## Commands

* !where: The bot will respond with "I'm here".
* !hello: The bot will say hi to whoever typed it
* !cd {duration in seconds}: Will start a countdown. If someone else types it then it will replace any existing countdowns
* !cd cancel: Will cancel a running countdown

## Acknowledgement

I wrote this code from scratch. While I'll happy to share this code, please acknowledge my contribution by linking to [twitch.tv/three_mountaineers](https://www.twitch.tv/three_mountaineers)