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
6. Create
7. In the next screen, click on "Manage" in the new row that's been created
8. If step 4 didn't work, change the OAuth Redirect URL now.
9. Copy the "Client ID". Copy this somewhere.
10. Click on the "New Secret" button. Copy this somewhere AND DO NOT SHARE IT.

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

## Section 4: Let the chatbot act as you (or another account)

1. Hit "Windows" + "Q" key -> "Command Prompt"
2. Change directory to where you downloaded the code
3. Type the following into the "Command Prompt" window: `python -m mountaineer_bot.twitch_auth -c env.cfg`. You should see the first line to pop up is `* Serving Flask app 'twitch_auth'`
4. Open your browser and go to `http://localhost:3000/login/me`
5. You should get a twitch prompt, and the following:
    * Under the twitch logo, the name should be what you said Section 2, step 3.
    * The list of things it should ask you to allow should be and only be:
        * Send live Stream Chat and Rooms messages
        * View live Stream Chat and Rooms message
6. If the above checks out, hit authorize. Otherwise, don't.
7. Once you hit authorize, a few things will happen. It should then say "Successfully authorized using code flow." in your browser.
8. Go back to the "Command Prompt" window and hit `Ctrl + C`. Close the window.

Note: You can check the application in Twitch by going to your Settings -> Connections -> Other Connections. Disconnect when you don't need it anymore.

## Section 5: Start the chatbot

1. Hit "Windows+ "Q" key -> "Command Prompt"
2. Change directory to where you downloaded the code
3. Type the following into the "Command Prompt" window: `python -m mountaineer_bot.main -c env.cfg -u me`
4. You should see "Running in channels: {channels you listed}", then "Starting bot..." and then "{your username} is online!". If you see these, congrats, the bot is ready to go!
5. When you're finished, close the window you created in this section.

When you next want to use the bot, you only need to do Section 5.

## Additional notes

Keen eyed readers will see that in 4.4, the end of the URL has "me", and in 5.3 the parameter we pass for `-u` is also "me". They are in fact related, and you can call them whatever you want. So if you have multiple bot accounts, you can use them with this same code. Just run section 5 with a new configuration file that `-c` refers to, and a different user that `-u` refers to.

## Commands

* !where: The bot will respond with "I'm here".
* !hello: The bot will say hi to whoever typed it
* !cd {duration in seconds}: Will start a countdown. If someone else types it then it will replace any existing countdowns
* !cd cancel: Will cancel a running countdown