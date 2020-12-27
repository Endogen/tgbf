import os
import shutil
import logging
import importlib

import tgbf.emoji as emo
import tgbf.utils as utl
import tgbf.constants as con

from zipfile import ZipFile
from importlib import reload
from telegram import ParseMode, Chat, Update
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext, Handler
from telegram.error import InvalidToken, Unauthorized
from tgbf.config import ConfigManager


class TelegramBot:

    plugins = list()

    def __init__(self, config: ConfigManager, token):
        self.config = config

        read_timeout = self.config.get("telegram", "read_timeout")
        connect_timeout = self.config.get("telegram", "connect_timeout")
        con_pool_size = self.config.get("telegram", "con_pool_size")

        self.tgb_kwargs = dict()

        if read_timeout:
            self.tgb_kwargs["read_timeout"] = read_timeout
        if connect_timeout:
            self.tgb_kwargs["connect_timeout"] = connect_timeout
        if con_pool_size:
            self.tgb_kwargs["con_pool_size"] = con_pool_size

        try:
            self.updater = Updater(token, request_kwargs=self.tgb_kwargs, use_context=True)
        except InvalidToken as e:
            logging.error(f"ERROR: Bot token not valid: {e}")
            exit()

        try:
            # Check if Telegram token is really valid
            self.updater.bot.get_me()
        except Unauthorized as e:
            logging.error(f"ERROR: Bot token not valid: {e}")
            exit()

        self.job_queue = self.updater.job_queue
        self.dispatcher = self.updater.dispatcher

        # Load classes in folder 'plugins'
        self._load_plugins()

        # Handler for file downloads (plugin updates)
        mh = MessageHandler(Filters.document, self._update_plugin)
        self.dispatcher.add_handler(mh)

        # Handle all Telegram related errors
        self.dispatcher.add_error_handler(self._handle_tg_errors)

        # Send message to admin
        for admin in config.get("admin", "ids"):
            try:
                self.updater.bot.send_message(admin, f"{emo.ROBOT} Bot is up and running!")
            except Exception as e:
                msg = f"{emo.ERROR} Couldn't send 'Bot is up' message"
                logging.error(f"{msg}: {e}")

    def bot_start_polling(self):
        """ Start the bot in polling mode """
        self.updater.start_polling(clean=True)

    def bot_start_webhook(self):
        """ Start the bot in webhook mode """
        self.updater.start_webhook(
            listen=self.config.get("webhook", "listen"),
            port=self.config.get("webhook", "port"),
            url_path=self.updater.bot.token,
            key=self.config.get("webhook", "privkey_path"),
            cert=self.config.get("webhook", "cert_path"),
            webhook_url=f"{self.config.get('webhook', 'url')}:"
                        f"{self.config.get('webhook', 'port')}/"
                        f"{self.updater.bot.token}")

    def bot_idle(self):
        """ Go in idle mode """
        self.updater.idle()

    def add_plugin(self, module_name):
        """ Load a plugin so that it can be used """
        for plugin in self.plugins:
            if plugin.get_name() == module_name.lower():
                return {"success": False, "msg": "Plugin already active"}

        try:
            module_path = f"{con.DIR_SRC}.{con.DIR_PLG}.{module_name}.{module_name}"
            module = importlib.import_module(module_path)

            reload(module)

            msg = f"Method 'init' of plugin '{module_name}' has to " \
                  f"return one or more instances of {Handler.__name__}"

            with getattr(module, module_name.capitalize())(self) as plugin:
                handlers = plugin.init()

                if not isinstance(handlers, tuple):
                    handlers = (handlers,)
                if not all(isinstance(h, Handler) for h in handlers):
                    logging.error(msg)
                    return

                for handler in handlers:
                    self.dispatcher.add_handler(handler)
                    self.plugins.append(plugin)

                logging.info(f"Plugin '{plugin.get_name()}' added")
                return {"success": True, "msg": "Plugin added"}
        except Exception as ex:
            msg = f"Plugin '{module_name.capitalize()}' can't be added: {ex}"
            logging.error(msg)
            raise ex

    def remove_plugin(self, module_name):
        """ Unload a plugin so that it can't be used """
        for plugin in self.plugins:
            if plugin.get_name() == module_name.lower():
                try:
                    for handler in self.dispatcher.handlers[0]:
                        if isinstance(handler, CommandHandler):
                            if handler.command[0] == plugin.get_handle():
                                self.dispatcher.handlers[0].remove(handler)
                                break

                    self.plugins.remove(plugin)
                    logging.info(f"Plugin '{plugin.get_name()}' removed")
                    break
                except Exception as ex:
                    msg = f"Plugin '{module_name.capitalize()}' can't be removed: {ex}"
                    logging.warning(msg)
                    raise ex
        return {"success": True, "msg": "Plugin removed"}

    def _load_plugins(self):
        """ Load all plugins from the 'plugins' folder """
        try:
            for _, folders, _ in os.walk(os.path.join(con.DIR_SRC, con.DIR_PLG)):
                for folder in folders:
                    if folder.startswith("_"):
                        continue
                    self._load_plugin(f"{folder}.py")
                break
        except Exception as e:
            logging.error(e)

    def _load_plugin(self, file):
        """ Load a single plugin """
        try:
            module_name, extension = os.path.splitext(file)
            module_path = f"{con.DIR_SRC}.{con.DIR_PLG}.{module_name}.{module_name}"
            module = importlib.import_module(module_path)

            msg = f"Method 'init' of plugin '{module_name}' has to " \
                  f"return one or more instances of {Handler.__name__}"

            with getattr(module, module_name.capitalize())(self) as plugin:
                handlers = plugin.init()

                if not isinstance(handlers, tuple):
                    handlers = (handlers,)
                if not all(isinstance(h, Handler) for h in handlers):
                    logging.error(msg)
                    return

                for handler in handlers:
                    self.dispatcher.add_handler(handler)
                    self.plugins.append(plugin)

                logging.info(f"Plugin '{plugin.get_name()}' added")
        except Exception as e:
            logging.error(f"File '{file}': {e}")

    # TODO: Remove
    def _add_handler(self, plugin):
        """ Add CommandHandler for given plugin """
        handle = plugin.get_handle()

        if not isinstance(handle, str) or not plugin.get_handle():
            raise Exception("Wrong command handle")

        # TODO: Add possibility to add any handler. Maybe with decorators
        self.dispatcher.add_handler(
            CommandHandler(handle, plugin.check_and_execute, pass_args=True))

    def _update_plugin(self, bot, update):
        """
        Update a plugin by uploading a file to the bot.

        If you provide a .ZIP file then the content will be extracted into
        the plugin with the same name as the file. For example the file
        'about.zip' will be extracted into the 'about' plugin folder.

        It's also possible to provide a .PY file. In this case the file will
        replace the plugin implementation with the same name. For example the
        file 'about.py' will replace the same file in the 'about' plugin.

        All of this will only work in a private chat with the bot.
        """

        # Check if in a private chat
        if bot.get_chat(update.message.chat_id).type != Chat.PRIVATE:
            return

        # Check if user that triggered the command is allowed to execute it
        if update.effective_user.id not in self.config.get("admin", "ids"):
            return

        name = update.message.effective_attachment.file_name.lower()
        zipped = False

        try:
            if name.endswith(".py"):
                plugin_name = name.replace(".py", "")
            elif name.endswith(".zip"):
                if len(name) == 18:
                    msg = f"{emo.ERROR} Only backups of plugins are supported"
                    update.message.reply_text(msg)
                    return
                zipped = True
                if utl.is_numeric(name[:13]):
                    plugin_name = name[14:].replace(".zip", "")
                else:
                    plugin_name = name.replace(".zip", "")
            else:
                msg = f"{emo.ERROR} Wrong file format"
                update.message.reply_text(msg)
                return

            file = bot.getFile(update.message.document.file_id)

            if zipped:
                os.makedirs(con.DIR_TMP, exist_ok=True)
                zip_path = os.path.join(con.DIR_TMP, name)
                file.download(zip_path)

                with ZipFile(zip_path, 'r') as zip_file:
                    plugin_path = os.path.join(con.DIR_SRC, con.DIR_PLG, plugin_name)
                    zip_file.extractall(plugin_path)
            else:
                file.download(os.path.join(con.DIR_SRC, con.DIR_PLG, plugin_name, name))

            self.remove_plugin(plugin_name)
            self.add_plugin(plugin_name)

            shutil.rmtree(con.DIR_TMP, ignore_errors=True)

            update.message.reply_text(f"{emo.DONE} Plugin successfully loaded")
        except Exception as e:
            logging.error(e)
            msg = f"{emo.ERROR} {e}"
            update.message.reply_text(msg)

    def _handle_tg_errors(self, update: Update, context: CallbackContext):
        """ Handle errors for module 'telegram' and 'telegram.ext' """
        cls_name = f"Class: {type(self).__name__}"
        logging.error(f"{context.error} - {cls_name} - {update}")

        if not update:
            return

        error_msg = f"{emo.ERROR} *Telegram ERROR*: {context.error}"

        if update.message:
            update.message.reply_text(
                text=error_msg,
                parse_mode=ParseMode.MARKDOWN)
        elif update.callback_query:
            update.callback_query.message.reply_text(
                text=error_msg,
                parse_mode=ParseMode.MARKDOWN)
