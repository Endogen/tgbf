import os

DESCRIPTION = "Python Telegram Bot"

# Project folders
DIR_SRC = os.path.basename(os.path.dirname(__file__))
DIR_TEM = "templates"
DIR_PLG = "plugins"
DIR_RES = "res"
DIR_CFG = "cfg"
DIR_LOG = "log"
DIR_DAT = "dat"
DIR_TMP = "tmp"

# Project files
FILE_DAT = "global.db"
FILE_CFG = "config.json"
FILE_TKN = "token.json"
FILE_LOG = f"{DIR_SRC}.log"

# Max Telegram message length
MAX_TG_MSG_LEN = 4096
