import os
import sqlite3
import logging
import inspect
import threading

import tgbf.constants as c
import tgbf.emoji as emo

from pathlib import Path
from typing import List, Dict, Tuple, Callable
from telegram import ChatAction, Chat, Update, Message
from telegram.ext import CallbackContext, Handler
from telegram.ext.jobqueue import Job
from tgbf.config import ConfigManager
from tgbf.tgbot import TelegramBot
from datetime import datetime, timedelta
from tgbf.web import EndpointAction


class TGBFPlugin:

    def __init__(self, tg_bot: TelegramBot):
        self._bot = tg_bot

        # Set class name as name of this plugin
        self._name = type(self).__name__.lower()

        # Access to global config
        self._global_config = self._bot.config

        # Access to plugin config
        self._config = self.get_cfg_manager()

        # All bot handlers for this plugin
        self._handlers: List[Handler] = list()

        # All web endpoints for this plugin
        self._endpoints: Dict[str, EndpointAction] = dict()

    def __enter__(self):
        """ This method gets executed after __init__() but before
        load(). Make sure to return 'self' if you override it """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """ This method gets executed after __init__() and after load() """
        pass

    def load(self):
        """ This method will be executed after __init__() and
         after __enter__() but before __exit__(). It's typically
         used to add handlers and endpoints.

         It will not be executed if the configuration file of the
         plugin has the 'active = false' entry """

        method = inspect.currentframe().f_code.co_name
        msg = f"Method '{method}' of plugin '{self.name}' not implemented"
        logging.warning(msg)

    def cleanup(self):
        """ Overwrite this method if you want to clean something up
         before the plugin will be disabled """
        pass

    def callback_cfg_change(self, value, *keys):
        """ Overwrite this method if you need some logic to be executed
         after the plugin configuration changed """
        pass

    def get_cfg_manager(self, plugin: str = None, on_change: Callable = None, pass_args=True) -> ConfigManager:
        """ Returns a plugin configuration. If the config file
        doesn't exist then it will be created.

        If you don't provide 'plugin' and 'on_change' then the
        default callback_cfg_change() will be used as callback
        method that will be triggered on changes in the file.

        If 'pass_args' is True then the settings-change context
        (what has changed, key and value) will be passed to the
        callback method. If False then nothing will be passed. """

        if plugin:
            cfg_file = plugin.lower() + ".json"
            cfg_fold = os.path.join(self.get_cfg_path(plugin=plugin))
        else:
            cfg_file = f"{self.name}.json"
            cfg_fold = os.path.join(self.get_cfg_path())

            on_change = on_change if on_change else self.callback_cfg_change

        cfg_path = os.path.join(cfg_fold, cfg_file)

        # Create config directory if it doesn't exist
        os.makedirs(cfg_fold, exist_ok=True)

        # Create config file if it doesn't exist
        if not os.path.isfile(cfg_path):
            with open(cfg_path, 'w') as file:
                # Make it a valid JSON file
                file.write("{}")

        # Return plugin config
        return ConfigManager(
            cfg_path,
            callback=on_change,
            callback_pass_args=pass_args)

    @property
    def bot(self) -> TelegramBot:
        return self._bot

    @property
    def name(self):
        """ Return the name of the current plugin """
        return self._name

    @property
    def handle(self):
        """ Return the command string that triggers the plugin """
        handle = self.config.get("handle")
        return handle.lower() if handle else self.name

    @property
    def category(self):
        """ Return the category of the plugin for the 'help' command """
        return self.config.get("category")

    @property
    def description(self):
        """ Return the description of the plugin """
        return self.config.get("description")

    @property
    def plugins(self):
        """ Return a list of all active plugins """
        return self.bot.plugins

    @property
    def jobs(self):
        """ Return a tuple with all currently active jobs """
        return self.bot.job_queue.jobs()

    @property
    def global_config(self) -> ConfigManager:
        """ Return the global configuration """
        return self._global_config

    @property
    def config(self) -> ConfigManager:
        """ Return the configuration for this plugin """
        return self._config

    @property
    def handlers(self) -> List[Handler]:
        """ Return a list of bot handlers for this plugin """
        return self._handlers

    @property
    def endpoints(self) -> Dict[str, EndpointAction]:
        """ Return a dictionary with key = endpoint name and
        value = EndpointAction for this plugin """
        return self._endpoints

    def add_handler(self, handler: Handler, group: int = 0):
        """ Will add bot handlers to this plugins list of handlers
         and also add them to the bot dispatcher """

        self.bot.dispatcher.add_handler(handler, group)
        self.handlers.append(handler)

        logging.info(f"Plugin '{self.name}': {type(handler).__name__} added")

    def add_endpoint(self, name, endpoint: EndpointAction):
        """ Will add web endpoints (Flask) to this plugins list of
         endpoints and also add them to the Flask app """

        name = name if name.startswith("/") else "/" + name
        self.bot.web.app.add_url_rule(name, name, endpoint)
        self.endpoints[name] = endpoint

        logging.info(f"Plugin '{self.name}': Endpoint '{name}' added")

    def get_usage(self, replace: dict = None):
        """ Return how to use a command. Default resource '<plugin>.md'
         will be loaded from the resource folder and if you provide a
         dict with '<placeholder>,<value>' entries then placeholders in
         the resource will be replaced with the corresponding <value> """

        usage = self.get_resource(f"{self.name}.md")

        if usage:
            usage = usage.replace("{{handle}}", self.handle)

            if replace:
                for placeholder, value in replace.items():
                    usage = usage.replace(placeholder, str(value))

            return usage

        return None

    def get_global_resource(self, filename):
        """ Return the content of the given file
        from the global resource directory """

        path = os.path.join(os.getcwd(), c.DIR_RES, filename)
        return self._get_resource_content(path)

    def get_resource(self, filename, plugin=None):
        """ Return the content of the given file from
        the resource directory of the given plugin """

        path = os.path.join(self.get_res_path(plugin), filename)
        return self._get_resource_content(path)

    def _get_resource_content(self, path):
        """ Return the content of the file in the given path """

        try:
            with open(path, "r", encoding="utf8") as f:
                return f.read()
        except Exception as e:
            logging.error(e)
            self.notify(e)
            return None

    def get_jobs(self, name=None) -> Tuple['Job', ...]:
        """ Return jobs with given name or all jobs if not name given """

        if name:
            # Get all jobs with given name
            return self.bot.job_queue.get_jobs_by_name(name)
        else:
            # Return all jobs
            return self.bot.job_queue.jobs()

    def run_repeating(self, callback, interval, first=0, context=None, name=None):
        """ Executes the provided callback function indefinitely.
        It will be executed every 'interval' (seconds) time. The
        created job will be returned by this method. If you want
        to stop the job, execute 'schedule_removal()' on it.

        The job will be added to the job queue and the default
        name of the job (if no 'name' provided) will be the name
        of the plugin """

        return self.bot.job_queue.run_repeating(
            callback,
            interval,
            first=first,
            context=context,
            name=name if name else self.name)

    def run_once(self, callback, when, context=None, name=None):
        """ Executes the provided callback function only one time.
        It will be executed at the provided 'when' time. The
        created job will be returned by this method. If you want
        to stop the job before it gets executed, execute
        'schedule_removal()' on it.

        The job will be added to the job queue and the default
        name of the job (if no 'name' provided) will be the name
        of the plugin """

        return self.bot.job_queue.run_once(
            callback,
            when,
            context=context,
            name=name if name else self.name)

    def execute_global_sql(self, sql, *args):
        """ Execute raw SQL statement on the global
        database and return the result

        param: sql = the SQL query
        param: *args = arguments for the SQL query

        Following data will be returned
        If error happens:
        {"success": False, "data": None}

        If no data available:
        {"success": True, "data": None}

        If database disabled:
        {"success": False, "data": "Database disabled"} """

        db_path = os.path.join(os.getcwd(), c.DIR_DAT, c.FILE_DAT)
        return self._get_database_content(db_path, sql, *args)

    def execute_sql(self, sql, *args, plugin="", db_name=""):
        """ Execute raw SQL statement on database for given
        plugin and return the result.

        param: sql = the SQL query
        param: *args = arguments for the SQL query
        param: plugin = name of plugin that DB belongs too
        param: db_name = name of DB in case it's not the
        default (the name of the plugin)

        Following data will be returned
        If error happens:
        {"success": False, "data": None}

        If no data available:
        {"success": True, "data": None}

        If database disabled:
        {"success": False, "data": "Database disabled"} """

        if db_name:
            if not db_name.lower().endswith(".db"):
                db_name += ".db"
        else:
            if plugin:
                db_name = plugin + ".db"
            else:
                db_name = self.name + ".db"

        if plugin:
            plugin = plugin.lower()
            data_path = self.get_dat_path(plugin=plugin)
            db_path = os.path.join(data_path, db_name)
        else:
            db_path = os.path.join(self.get_dat_path(), db_name)

        return self._get_database_content(db_path, sql, *args)

    def _get_database_content(self, db_path, sql, *args):
        """ Open database connection and execute SQL statement """

        res = {"success": None, "data": None}

        # Check if database usage is enabled
        if not self.global_config.get("database", "use_db"):
            res["data"] = "Database disabled"
            res["success"] = False
            return res

        timeout = self.global_config.get("database", "timeout")
        db_timeout = timeout if timeout else 5

        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(db_path)
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            res["data"] = str(e)
            res["success"] = False
            logging.error(e)
            self.notify(e)

        con = None
        cur = None

        try:
            con = sqlite3.connect(db_path, timeout=db_timeout)
            cur = con.cursor()
            cur.execute(sql, args)
            con.commit()

            res["data"] = cur.fetchall()
            res["success"] = True
        except Exception as e:
            res["data"] = str(e)
            res["success"] = False
            logging.error(e)
            self.notify(e)
        finally:
            if cur:
                cur.close()
            if con:
                con.close()

            return res

    def global_table_exists(self, table_name):
        """ Return TRUE if given table exists in global database, otherwise FALSE """

        db_path = os.path.join(os.getcwd(), c.DIR_DAT, c.FILE_DAT)
        return self._database_table_exists(db_path, table_name)

    def table_exists(self, table_name, plugin=None, db_name=None):
        """ Return TRUE if given table existsin given plugin, otherwise FALSE """

        if db_name:
            if not db_name.lower().endswith(".db"):
                db_name += ".db"
        else:
            if plugin:
                db_name = plugin + ".db"
            else:
                db_name = self.name + ".db"

        if plugin:
            db_path = os.path.join(self.get_dat_path(plugin=plugin), db_name)
        else:
            db_path = os.path.join(self.get_dat_path(), db_name)

        return self._database_table_exists(db_path, table_name)

    def _database_table_exists(self, db_path, table_name):
        """ Open connection to database and check if given table exists """

        if not Path(db_path).is_file():
            return False

        con = sqlite3.connect(db_path)
        cur = con.cursor()
        exists = False

        statement = self.get_global_resource("table_exists.sql")

        try:
            if cur.execute(statement, [table_name]).fetchone():
                exists = True
        except Exception as e:
            logging.error(e)
            self.notify(e)

        con.close()
        return exists

    def get_res_path(self, plugin=None):
        """ Return path of resource directory for this plugin """
        if not plugin:
            plugin = self.name
        return os.path.join(c.DIR_SRC, c.DIR_PLG, plugin, c.DIR_RES)

    def get_cfg_path(self, plugin=None):
        """ Return path of configuration directory for this plugin """
        if not plugin:
            plugin = self.name
        return os.path.join(c.DIR_SRC, c.DIR_PLG, plugin, c.DIR_CFG)

    def get_dat_path(self, plugin=None):
        """ Return path of data directory for this plugin """
        if not plugin:
            plugin = self.name
        return os.path.join(c.DIR_SRC, c.DIR_PLG, plugin, c.DIR_DAT)

    def get_plg_path(self, plugin=None):
        """ Return path of current plugin directory """
        if not plugin:
            plugin = self.name
        return os.path.join(c.DIR_SRC, c.DIR_PLG, plugin)

    def plugin_available(self, plugin_name):
        """ Return TRUE if the given plugin is enabled or FALSE otherwise """
        for plugin in self.plugins:
            if plugin.name == plugin_name.lower():
                return True
        return False

    def remove_msg(self, message: Message, after_secs, private=True, public=True):
        """ Remove a Telegram message after a given time """

        is_private = self.bot.updater.bot.get_chat(message.chat_id).type == Chat.PRIVATE

        def remove_msg_job(context: CallbackContext):
            param_lst = str(context.job.context).split("_")
            chat_id = param_lst[0]
            msg_id = param_lst[1]

            try:
                context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception as e:
                logging.error(f"Not possible to remove message: {e}")

        def remove():
            self.run_once(
                remove_msg_job,
                datetime.utcnow() + timedelta(seconds=after_secs),
                context=f"{message.chat_id}_{message.message_id}")

        if (is_private and private) or (not is_private and public):
            remove()

    def notify(self, some_input):
        """ All admins in global config will get a message with the given text.
         Primarily used for exceptions but can be used with other inputs too. """

        if isinstance(some_input, Exception):
            some_input = repr(some_input)

        if self.global_config.get("admin", "notify_on_error"):
            for admin in self.global_config.get("admin", "ids"):
                try:
                    msg = f"{emo.ALERT} Admin Notification {emo.ALERT}\n{some_input}"
                    self.bot.updater.bot.send_message(admin, msg)
                except Exception as e:
                    error = f"Not possible to notify admin id '{admin}'"
                    logging.error(f"{error}: {e}")
        return some_input

    @classmethod
    def private(cls, func):
        """ Decorator for methods that need to be run in a private chat with the bot """

        def _private(self, update: Update, context: CallbackContext, **kwargs):
            if self.config.get("private") == False:
                return func(self, update, context, **kwargs)
            elif context.bot.get_chat(update.message.chat_id).type == Chat.PRIVATE:
                return func(self, update, context, **kwargs)
            else:
                try:
                    name = context.bot.username if context.bot.username else context.bot.name
                    msg = f"{emo.INFO} Only allowed to execute in a private chat with @{name}"
                    update.message.reply_text(msg)
                except:
                    pass

        return _private

    @classmethod
    def public(cls, func):
        """ Decorator for methods that need to be run in a public group """

        def _public(self, update: Update, context: CallbackContext, **kwargs):
            if self.config.get("public") == False:
                return func(self, update, context, **kwargs)
            elif context.bot.get_chat(update.message.chat_id).type != Chat.PRIVATE:
                return func(self, update, context, **kwargs)
            else:
                try:
                    msg = f"{emo.INFO} Only allowed to execute in a public chat"
                    update.message.reply_text(msg)
                except:
                    pass

        return _public

    @classmethod
    def owner(cls, func):
        """
        Decorator that executes the method only if the user is an bot admin.

        The user ID that triggered the command has to be in the ["admin"]["ids"]
        list of the global config file 'config.json' or in the ["admins"] list
        of the currently used plugin config file.
        """

        def _owner(self, update: Update, context: CallbackContext, **kwargs):
            if self.config.get("owner") == False:
                return func(self, update, context, **kwargs)

            user_id = update.effective_user.id

            admins_global = self.global_config.get("admin", "ids")
            if admins_global and isinstance(admins_global, list):
                if user_id in admins_global:
                    return func(self, update, context, **kwargs)

            admins_plugin = self.config.get("admins")
            if admins_plugin and isinstance(admins_plugin, list):
                if user_id in admins_plugin:
                    return func(self, update, context, **kwargs)

        return _owner

    @classmethod
    def dependency(cls, func):
        """ Decorator that executes a method only if the mentioned
        plugins in the config file of the current plugin are enabled """

        def _dependency(self, update: Update, context: CallbackContext, **kwargs):
            dependencies = self.config.get("dependencies")

            if dependencies and isinstance(dependencies, list):
                plugin_names = [p.name for p in self.plugins]

                for dependency in dependencies:
                    if dependency.lower() not in plugin_names:
                        msg = f"{emo.ERROR} Plugin '{self.name}' is missing dependency '{dependency}'"
                        update.message.reply_text(msg)
                        return
            else:
                logging.error(f"Dependencies for plugin '{self.name}' not defined as list")

            return func(self, update, context, **kwargs)
        return _dependency

    @classmethod
    def send_typing(cls, func):
        """ Decorator for sending typing notification in the Telegram chat """
        def _send_typing(self, update: Update, context: CallbackContext, **kwargs):
            if update.message:
                user_id = update.message.chat_id
            elif update.callback_query:
                user_id = update.callback_query.message.chat_id
            else:
                logging.warning(f"Can not extract user ID - {update}")
                return func(self, update, context, **kwargs)

            try:
                context.bot.send_chat_action(
                    chat_id=user_id,
                    action=ChatAction.TYPING)
            except:
                pass

            return func(self, update, context, **kwargs)
        return _send_typing

    @staticmethod
    def threaded(fn):
        """ Decorator for methods that have to run in their own thread """
        def _threaded(*args, **kwargs):
            return threading.Thread(target=fn, args=args, kwargs=kwargs).start()
        return _threaded
