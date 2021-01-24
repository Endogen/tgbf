# TGBF Plugins
General info about plugins and specific info about plugins that are included per default

Every plugin can add different handlers (from {PTB}[https://github.com/python-telegram-bot/python-telegram-bot]) and web endpoints ({Flask}[https://github.com/pallets/flask])

## Plugin conventions
Plugins will be automatically recognized and added on startup if:
- Plugin has own folder in `tgbf/plugins`
- Folder name == plugin name
- Plugin folder needs to have a `<plugin name>.py` file (== plugin itself)
- Plugin class name == plugin name (but first letter in uppercase)

## Plugin configuration
A plugin configuration file can be empty or even not existing. If you provide a config, following keys are recognized automatically:

- `dependencies`: Needs to be a list. It should consist of plugin names that need to be active in order to be able to use the current plugin
- `handle`: If the plugin handle should be differnt from the plugin name then provide it here
- `category`: If you want to list the plugin in the /help command, then provide a category
- `description`: If you want to list the plugin in the /help command, then provide a description
- `private`: If you use the "private" decorator in your plugin then you can disable it if you set `private = false` in the config
- `public`: If you use the "public" decorator in your plugin then you can disable it if you set `public = false` in the config
- `owner`: If you use the "owner" decorator in your plugin then you can disable it if you set `owner = false` in the config
- `admins`: Needs to be a list. If you use the "owner" decorator in your plugin then you can add admins for this plugin by adding Telegram IDs as Integers to the list
- `active`: If you set `active = false` then the plugin will not be loaded next time the bot (re-)starts

## Implementation details
- Plugin needs to inherit from class `TGBFPlugin`
- Plugin needs to overwrite `load` method

The `load` method usually adds bot handlers that allow interactions with commands etc.

## Default plugins
This is a list of out-of-the-box available plugins for this bot

### About
Shows the creator and purpose of the bot and some additional info

### Admin
Manage the bot over Telegram. Includes:
- Enabling / disabling plugins at runtime
- Execute raw SQL queries on plugin DBs or the global DB
- Set / get values from global / plugin configuration(s)

### Backup
Can backup the whole bot or a single plugin and provides a Telegram download of the backup

### Debug
Shows you critical information that you might need for debugging the bot. It will show you:
- Public IP address of the server
- Nr. of currently open files on the server

### Feedback
Allows any user to provide feedback to the bot developer

### Help
Lists all plugins that have a `description` and `category` entry in the config file

### Logfile
Provides a download of the current logfile over Telegram

### Shutdown
Let's you shutdown the bot remotely

### Start
The content of this command will be shown to new users of the bot that accepted to interact with it

### Usage
Is not a command like most of the other plugins. It saves the usage of all issued commands for later analysis. Something like an activity log.