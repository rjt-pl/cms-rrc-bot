
### Source Files

* **utils.py** - Some smaller utility classes/methods, like to manage json files or make sure only admins can use certain commands.

* **cogs/questionnaire.py** - All the logic for the questionnaire, that is: !senbutton command, !forumtags command, questionnaire itself, approving/rejecting/editing answers, sending it to the forum.

* **cogs/admin.py** - Only a reload command, does not really need to be used frequently, mainly for debugging but nice to have.

* **logger.py** - Custom implementation for the logging of basically everything important like: `[2023-06-28 ...] [INFO   ] discord.client: ...`

* **main.py** - Used to run the file, loads the config.json file and creates the bot instance, not much else.

* **bot.py** - File that only has the Bot class. 

### Getting Emoji IDs

`\:Emoji_Name:` -- Prints the ID of the specified emoji

See (setup.md)[setup.md] for more information.
