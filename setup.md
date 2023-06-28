	Bot Setup:
1. Go to "https://discord.com/developers/applications" and make sure you're logged in.
2. Click "New Application" (top right, left of your profile picture).
3. Go to the "Bot" tab (left side, under settings).
4. Click "Add Bot", then "Reset Token", save this token somewhere to use later.

    MTEyMzY5Nzc4MzMyNTU5Mzc0MQ.GzOqr3.cSeKCCXfb_Zw3UuTGqdRi5Ino_Q0eLfTijDc9U
    
5. Scroll down until you see "Privileged Gateway Intents", enable all 3 intents:
	- "PRESENCE INTENT"
	- "SERVER MEMBERS INTENT"
	- "MESSAGE CONTENT INTENT"
6. Go to the "OAtuh2" tab, above the "Bot" tab, click on "URL Generator".
7. In the "SCOPES" section, enable 2 scopes and NOTHING ELSE:
	- "bot" (middle row, 4th from above)
	- "application.commands" (right row, at the top)
8. Scroll down to "BOT PERMISSIONS", click the permissions you want your bot to have, if the bot is
going to be in a server that you own yourself, I would suggest enabling "Administrator" and nothing else.
9. Scroll down and copy the URL, paste that in a new tab in your webbrowser and add it to your server(s).

Bot string: https://discord.com/api/oauth2/authorize?client_id=1123697783325593741&permissions=8&scope=bot%20applications.commands

	Script Setup:
1. Make sure you have python 3.9 or above installed: https://www.python.org/downloads/
2. Open up CMD and type in "pip install discord", and press Enter.
3. Head over to the zip file I attached with this and open the "config.json" file in any editor you want (can be .txt).
4. Change the value to the right of "token" with your bots token that you saved prior.
5. Change the ids in the variable "owner_ids" with the discord user ids of anyone you trust with this bot.
Not doing so will result in the bot refusing to let you run the commands.
6. Save the file (probably CTRL+s) and run the "main.py" file, the bot should now appear as online on discord.
7. Enjoy your bot!
