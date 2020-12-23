# T2X-Bot
T2X-Bot is a Telegram bot created by @endogen for the T2X community. Visit the [website](http://t2xtoken.io) to learn more about it.

## Overview
The bot is build around the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) module and is polling based. [Webhook mode](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks) is implemented but untested.

### General bot features
* Every command is a plugin
* Every plugin can be enabled / disabled without restarting the bot
* Every plugin can be updated by drag & dropping the implementation into the bot chat
* Restart or shutdown the bot via command
* Bot can be administered by more then one user
* Bot can send current logfile over Telegram
* Admin can query data from the various databases directly over Telegram
* Bot has a web-interface so that data can be accessed also over JSON

## Configuration
This part is only relevant if you want to host this bot yourself. If you just want to use the bot, [add the bot](https://t.me/t2x_robot) *@t2x_robot* to your Telegram contacts.

Before starting up the bot you have to take care of some settings and add a Telegram API token. The configuration file, toke file and wallet file are located in the `config` folder.

### config.json
This file holds the configuration for the bot. You have to at least edit the value for __admin_id__. Everything else is optional.

- __admin - ids__: This is a list of Telegram user IDs that will be able to control the bot. You can add your own user or multiple users if you want. If you don't know your Telegram user ID, get in a conversation with Telegram bot [@userinfobot](https://t.me/userinfobot) and if you write him (anything) he will return you your user ID.
- __admin - notify_on_error__: If set to `true` then all user IDs in the "admin - ids" list will be notified if some error comes up.
- __telegram - read_timeout__: Read timeout in seconds as integer. Usually this value doesn't have to be changed.
- __telegram - connect_timeout__: Connect timeout in seconds as integer. Usually this value doesn't have to be changed.
- __webhook - listen__: Required only for webhook mode. IP to listen to.
- __webhook - port__: Required only for webhook mode. Port to listen on.
- __webhook - privkey_path__: Required only for webhook mode. Path to private key  (.pem file).
- __webhook - cert_path__: Required only for webhook mode. Path to certificate (.pem file).
- __webhook - url__: Required only for webhook mode. URL under which the bot is hosted.
- __database__ - __use_db__: If `true` then new database files (SQLite) will be created if a plugin tries to execute some SQL statements. If `false`, no databases will be used.

### token.json
This file holds the Telegram bot token. You have to provide one and you will get it in a conversation with Telegram bot [@BotFather](https://t.me/BotFather) while registering your bot.

If you don't want to provide the token in a file then you have two other options:
- Provide it as a command line argument: `-tkn <your token>`
- Provide it as an input on the command line (**MOST SECURE**): `-input-tkn`

### wallet.json
This file holds the private key of the TRX wallet that belongs to the bot and from which payouts will be send to users.

## Usage
In order to run the bot you need to execute it with the Python interpreter. If you don't have any idea where to host the bot, take a look at [Where to host Telegram Bots](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Where-to-host-Telegram-Bots). Services like [Heroku](https://www.heroku.com) (free) will work fine. You can also run the script locally on your own computer for testing purposes.

### Prerequisites
##### Python version
You have to use at least __Python 3.7__ to execute the scripts. Older versions are not supported.

##### Installing needed modules from `requirements.txt`
In order to be able to run the bot you will need to install some dependencies.

Install all needed Python modules

```shell
pip3 install -r requirements.txt
```

### Starting
First you have to make the script `run.sh` executable with

```shell
chmod +x run.sh
```

Then run it to get the bot up with

```shell
./run.sh &
```

### Stopping
The recommended way to stop the bot is by using the bot command `/shutdown` (only possible for admins). If you don't want or can't use the command, you can shut the bot down with:

```shell
pkill python3.7
```

which will kill __every__ Python 3.7 process that is currently running.

### Autocomplete for commands
If you want to show a list of available commands as you type, open a chat with Telegram bot [@BotFather](https://t.me/BotFather) and execute the command `/setcommands`. Then choose the bot you want to activate the list for and after that send the list of commands with description. Something like this:

```
balance - Show TRX and T2X balance
deposit - Show wallet address and qr-code
feedback - Send us your feedback
help - Show all available commands
rain - Let it rain T2X on users
send_t2x - Send T2X from your wallet
send_trx - Send TRX from your wallet
tip_t2x - Tip another user with T2X
tip_trx - Tip another user with TRX
withdraw_t2x - Withdraw all T2X from your wallet
withdraw_trx - Withdraw all TRX from your wallet
```


## Development
The bot is under active development and not considered finished yet. If you want to help out you can report issues or create PRs.

### Plugins
If you decide to write your own plugin, check out the [Plugin Page](https://github.com/Endogen/T2X-Bot/tree/master/t2xbot/plugins) to read up on how to create a plugin and know about available plugins.

### Support
If you'd like to support the project, consider donating T2X tokens to this address:  
`TMMeFzXfVDPoGbSpSyXRNfTnhUZS7m8aRs`

Or use the referral link:  
[https://t2xtoken.io/?ref=TMMeFzXfVDPoGbSpSyXRNfTnhUZS7m8aRs](https://t2xtoken.io/?ref=TMMeFzXfVDPoGbSpSyXRNfTnhUZS7m8aRs)
