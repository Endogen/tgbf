import os
import json
import logging

from threading import Thread
from watchgod import watch, Change
from collections.abc import Callable


class ConfigManager(Thread):

    # JSON content
    _cfg = dict()
    # Config file path
    _cfg_file = None
    # Function to trigger on changes
    _callback = None
    # Pass changed key & value args to callback?
    _callback_pass_args = False
    # Ignore reloading config?
    _ignore = False

    def __init__(self, config_file, callback: Callable = None, callback_pass_args=True):
        """ This class takes a JSON config file and makes it available
         so that if you provide a key, you will get the value back.
         Values can also bet set or removed from the config. Setting
         and removing values will be written to the initial config file.

         The config file will automatically be watched for changes
         and re-read if something changes.

         You can provide a callback function that will be triggered
         if the content of the config changes. The callback function
         runs in it's own thread and will get following arguments if
         callback_pass_args=True:

         config file content changes -> callback(self._cfg, None, None)
         new value set for key -> callback(self._cfg, value, *keys)
         keys removed -> callback(self._cfg, None, *keys)

         If callback_pass_args=False then callback function will be
         called without passing arguments.
         """

        Thread.__init__(self)

        if config_file:
            self._cfg_file = config_file
        else:
            logging.error("ERROR: No config file provided")

        self._callback = callback
        self._callback_pass_args = callback_pass_args

        self.start()

    def run(self) -> None:
        """ Watch for config file changes """

        for change in watch(self._cfg_file):
            for status, location in change:
                if status == Change.modified and location == self._cfg_file:
                    self.on_modified()

    def on_modified(self):
        """ Will be triggered if the config file has been changed manually.
         Will also execute the callback method if there is one """

        if self._ignore:
            self._ignore = False
        else:
            self._read_cfg()

            if callable(self._callback):
                if self._callback_pass_args:
                    Thread(target=self._callback(self._cfg, None, None)).start()
                else:
                    Thread(target=self._callback()).start()

    def _read_cfg(self):
        """ Read the JSON content of a given configuration file """

        try:
            if os.path.isfile(self._cfg_file):
                with open(self._cfg_file) as config_file:
                    self._cfg = json.load(config_file)
        except Exception as e:
            err = f"Can't read '{self._cfg_file}'"
            logging.error(f"{repr(e)} - {err}")

    def _write_cfg(self):
        """ Write the JSON dictionary into the given configuration file """

        try:
            if not os.path.exists(os.path.dirname(self._cfg_file)):
                os.makedirs(os.path.dirname(self._cfg_file))
            with open(self._cfg_file, "w") as config_file:
                json.dump(self._cfg, config_file, indent=4)
        except Exception as e:
            err = f"Can't write '{self._cfg_file}'"
            logging.error(f"{repr(e)} - {err}")

    def get(self, *keys):
        """ Return the value of the given key(s) from a configuration file """

        if not self._cfg:
            self._read_cfg()

        if not keys:
            return self._cfg

        value = self._cfg

        try:
            for key in keys:
                value = value[key]
        except Exception as e:
            err = f"Can't get '{keys}' from '{self._cfg_file}'"
            logging.debug(f"{repr(e)} - {err}")
            return None

        return value

    def set(self, value, *keys):
        """ Set a new value for the given key(s) in the configuration file.
        Will also execute the callback method if there is one """

        if not self._cfg:
            self._read_cfg()

        if not keys:
            return

        tmp_cfg = self._cfg

        try:
            for key in keys[:-1]:
                tmp_cfg = tmp_cfg.setdefault(key, {})
            tmp_cfg[keys[-1]] = value

            self._ignore = True
            self._write_cfg()

            if callable(self._callback):
                if self._callback_pass_args:
                    Thread(target=self._callback(self._cfg, value, *keys)).start()
                else:
                    Thread(target=self._callback()).start()
        except Exception as e:
            err = f"Can't set '{keys}' in '{self._cfg_file}'"
            logging.debug(f"{repr(e)} - {err}")

    def remove(self, *keys):
        """ Remove given key(s) from the configuration file.
        Will also execute the callback method if there is one """

        if not self._cfg:
            self._read_cfg()

        if not keys:
            return

        tmp_cfg = self._cfg

        try:
            for key in keys[:-1]:
                tmp_cfg = tmp_cfg.setdefault(key, {})
            del tmp_cfg[keys[-1]]

            self._ignore = True
            self._write_cfg()

            if callable(self._callback):
                if self._callback_pass_args:
                    Thread(target=self._callback(self._cfg, None, *keys)).start()
                else:
                    Thread(target=self._callback()).start()
        except KeyError as e:
            err = f"Can't remove key '{keys}' from '{self._cfg_file}'"
            logging.debug(f"{repr(e)} - {err}")
