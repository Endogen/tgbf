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
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from telegram.error import InvalidToken, Unauthorized
from tgbf.config import ConfigManager
from tgbf.web import FlaskAppWrapper, EndpointAction


class TelegramBot:

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

        # TODO: Reload / restart flask at runtime
        #  https://gist.github.com/nguyenkims/ff0c0c52b6a15ddd16832c562f2cae1d

        # Init web interface
        port = self.config.get("web", "port")
        self.web = FlaskAppWrapper(__name__, port)

        # TODO: Add this route after restart of flask
        # Add default web endpoint
        action = EndpointAction(None, None)
        self.web.app.add_url_rule("/", "/", action)

        # Load classes from folder 'plugins'
        self.plugins = list()
        self._load_plugins()

        # Handler for file downloads (plugin updates)
        mh = MessageHandler(Filters.document, self._update_plugin)
        self.dispatcher.add_handler(mh)

        # Handle all Telegram related errors
        self.dispatcher.add_error_handler(self._handle_tg_errors)

        # Send message to admin(s)
        for admin in config.get("admin", "ids"):
            try:
                self.updater.bot.send_message(admin, f"{emo.ROBOT} Bot is up and running!")
            except Exception as e:
                msg = f"ERROR: Couldn't send 'Bot is up' message"
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

    def start_web(self):
        """ Start web interface """
        if self.config.get("web", "use_web"):
            self.web.run()

    def bot_idle(self):
        """ Go in idle mode """
        self.updater.idle()

    def enable_plugin(self, name):
        """ Load a single plugin """

        try:
            module_name, _ = os.path.splitext(name)
            module_path = f"{con.DIR_SRC}.{con.DIR_PLG}.{module_name}.{module_name}"
            module = importlib.import_module(module_path)

            reload(module)

            with getattr(module, module_name.capitalize())(self) as plugin:
                active = plugin.config.get("active")
                if active is not None and active is False:
                    msg = f"Plugin '{name}' not enabled"
                    logging.info(msg)
                    return False, msg

                try:
                    plugin.load()

                    self.plugins.append(plugin)
                    msg = f"Plugin '{plugin.name}' enabled"
                    logging.info(msg)
                    return True, msg
                except Exception as e:
                    msg = f"ERROR: Plugin '{plugin.name}' load() failed: {e}"
                    logging.error(msg)
                    return False, str(e)
        except Exception as e:
            msg = f"ERROR: Plugin '{name}' can not be enabled: {e}"
            logging.error(msg)
            return False, str(e)

    def disable_plugin(self, module_name):
        """ Remove a plugin from the plugin list and also
         remove all its handlers from the dispatcher """

        for plugin in self.plugins:
            if plugin.name == module_name.lower():

                # Remove endpoints (currently not possible)
                if plugin.endpoints:
                    msg = f"Not possible to disable a plugin that has an endpoint"
                    logging.info(msg)
                    return False, msg

                # Remove bot handlers
                for handler in plugin.handlers:
                    for group, handler_list in self.dispatcher.handlers.items():
                        if handler in handler_list:
                            self.dispatcher.remove_handler(handler, group)
                            break

                # Remove plugin from list of all plugins
                self.plugins.remove(plugin)

                try:
                    # Run plugins cleanup method
                    plugin.cleanup()
                except Exception as e:
                    msg = f"Plugin '{plugin.name}' cleanup failed: {e}"
                    logging.error(msg)
                    return False, str(e)

                msg = f"Plugin '{plugin.name}' disabled"
                logging.info(msg)
                return True, msg

    def _load_plugins(self):
        """ Load all plugins from the 'plugins' folder """

        try:
            for _, folders, _ in os.walk(os.path.join(con.DIR_SRC, con.DIR_PLG)):
                for folder in folders:
                    if folder.startswith("_"):
                        continue
                    self.enable_plugin(f"{folder}.py")
                break
        except Exception as e:
            logging.error(e)

    def _update_plugin(self, update: Update, context: CallbackContext):
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
        if context.bot.get_chat(update.message.chat_id).type != Chat.PRIVATE:
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

            file = context.bot.getFile(update.message.document.file_id)

            if zipped:
                os.makedirs(con.DIR_TMP, exist_ok=True)
                zip_path = os.path.join(con.DIR_TMP, name)
                file.download(zip_path)

                with ZipFile(zip_path, 'r') as zip_file:
                    plugin_path = os.path.join(con.DIR_SRC, con.DIR_PLG, plugin_name)
                    zip_file.extractall(plugin_path)
            else:
                file.download(os.path.join(con.DIR_SRC, con.DIR_PLG, plugin_name, name))

            self.disable_plugin(plugin_name)
            self.enable_plugin(plugin_name)

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
