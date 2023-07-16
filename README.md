# RRC Bot

This Discord bot runs the IRR submission and approval functions for the
Champion Motorsports Race Review Committee (CMS RRC). It is programmed with
[discord.py](https://discordpy.readthedocs.io/en/latest/) and
[COGS](https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html).

### Source Files

* [utils.py](utils.py): Some smaller utility classes/methods, like to manage json files or make sure only admins can use certain commands.
* [cogs/questionnaire.py](cogs/questionnaire.py): All the logic for the questionnaire, that is: questionnaire itself, approving/rejecting/editing answers, sending it to the forum.
* [cogs/admin.py](cogs/admin.py): All admin functions (commands).
* [logger.py](logger.py): Custom logger, outputs to STDOUT only.
* [main.py](main.py): Used to start the bot, loads the config.json file and creates the bot instance.
* [bot.py](bot.py): Bot class.
* [extras/run_rrc_bot.sh](extras/run_rrc_bot.sh): **Startup script.** This wrapper script performs additional functions such as cloning the source code repository and checking for updates.

### Getting Emoji IDs

This is currently only useful for the button label of the Submit Protest
button. Type `\:Emoji_Name:` on the server, and it'll print the ID of the
specified emoji.

### Initial Setup

See (setup.md)[setup.md] for more information on initial setup, including
registering a new Discord application. **This has already been done** and
should not be necessary to repeat.

### Deployment (a.k.a. if Ryan gets hit by a bus)

This bot has been deployed on a Linux VPS managed by Ryan Thompson. To
re-deploy, kill the old bot first. These instructions assume a Debian/Ubuntu
Linux system. It's very possible to deploy elsewhere, but in that case you'll
probably want to follow the directions of your bot hosting provider.

1. Put a copy of `run_rrc_bot.sh` into the home directory of a user on the host system.
2. Run `ssh-keygen` on the host and copy `id_rsa.pub` to your GitHub account, or to a fork of this repository.
2. Run `sudo apt install github python3 monit`
3. Copy `extras/cms-rrc-bot` to `/etc/monit/conf-enabled`
4. `ssh user@host ./run_rrc_bot.sh`
5. Configure the bot (edit `config/` to taste, taking care to copy the sample
   config to a new `config.json`, and edit the bot key and all the various
   IDs to match those on the RRC server.
6. Run step 4 again. The bot should now be running.

### Management and Fault Tolerance

In the event of a crash, the bot will auto-restart itself via monit. To
start/restart manually, consult the [monit
manual](https://mmonit.com/monit/documentation/monit.html)

### Logging

To see the live status of the bot, run `tail -F repo_path/cms-rrc-bot.log`

## Author and Copyright

(c)2023 Ryan Thompson <i@ry.ca>

Limited license to David Anderson of Champion Motorsports
to use, modify, and deploy this code for non-commercial
purposes in conjunction with the Race Review Committee
(Stewards) at Champion Motorsports (cmsracing.com). 

Any other use is not allowed, unless you receive express
written permission from me via email.
