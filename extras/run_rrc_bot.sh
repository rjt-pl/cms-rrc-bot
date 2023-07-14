#!/bin/sh
#
# run_rrc_bot.sh - Run the bot and update the source
#
# This script will look for changes in the git repo, update if necessary,
# and launch (or kill and re-launch) the bot.
#
# Usage:
# Install dependencies on host.
# Install SSH keys from host to GitHub
# Edit the config variables first.
# scp run_rrc_bot.sh user@host:path
# ssh user@host path/run_rrc_bot.sh
#
# Run the script whenever
#
# 2023 Ryan Thompson <i@ry.ca>

#
# Config variables
#
REPO=rjt-pl/cms-rrc-bot
BASE=~/cms-rrc-bot
PID=$BASE/cms-rrc-bot.pid
LOG=$BASE/cms-rrc-bot.log

# Clone repo if $BASE doesn't exist yet
if [ ! -d $BASE ]; then
    echo "Repository not found. Cloning..."
    git clone git@github.com:$REPO.git $BASE

    if [ "$?" -ne 0 ]; then
        echo "Clone failed. Ensure you've run ssh-keygen and that your"
        echo "~/.ssh/id_rsa.pub has been added to GitHub at:"
        echo "https://github.com/rjt-pl/cms-rrc-bot/settings/keys/new"
        exit 2
    fi

    echo "Repository successfully cloned. You now need to supply"
    echo "a configuration for the bot in $BASE/config"
    exit 2
fi

# Repo is there; make sure it is up-to-date with origin/main
cd $BASE

echo "Updating repo from origin..."
git fetch origin
git merge origin/main
echo "Source code now up to date."

# Kill the bot if it's running
if [ -f $PIDFILE ]; then
    PID=`cat $PIDFILE`
    echo "Pidfile found with pid $PID"

    ps --pid "$PID" > /dev/null
    if [ "$?" -eq 0 ]; then
        echo "Process still running. Sending TERM..."
        kill -TERM $PID
        sleep 1

        ps --pid "$PID" > /dev/null
        if [ "$?" -eq 0 ]; then
            echo "Process didn't die. Sending KILL."
            kill -9 $PID
            sleep 1
        fi
    fi
fi

# Run the bot
echo "Starting process"
./main.py 2>&1 >>$LOG &
