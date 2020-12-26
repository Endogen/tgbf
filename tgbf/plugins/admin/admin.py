import os
import logging
import tgbf.utils as utl
import tgbf.emoji as emo

from telegram import ParseMode, Update
from telegram.ext import CallbackContext, CommandHandler
from tgbf.config import ConfigManager
from tgbf.plugin import TGBFPlugin


# TODO: Add possibility to reload config file of plugin
# TODO: Error if only one argument provided
class Admin(TGBFPlugin):

    def init(self):
        return CommandHandler(self.get_name(), self.admin_callback)

    def admin_callback(self, update: Update, context: CallbackContext):
        import time
        time.sleep(10)

        if not context.args:
            update.message.reply_text(
                text=f"Usage:\n{self.get_usage()}",
                parse_mode=ParseMode.MARKDOWN)
            return

        command = context.args[0].lower()
        context.args.pop(0)

        plugin = context.args[0].lower()
        context.args.pop(0)

        # ---- Execute raw SQL ----
        if command == "sql":
            db = context.args[0].lower()
            context.args.pop(0)

            sql = " ".join(context.args)
            res = self.execute_sql(sql, plugin=plugin, db_name=db)

            if res["success"]:
                if res["data"]:
                    msg = '\n'.join(str(s) for s in res["data"])
                else:
                    msg = f"{emo.INFO} No data returned"
            else:
                msg = f"{emo.ERROR} {res['data']}"

            update.message.reply_text(msg)

        # ---- Change configuration ----
        elif command == "cfg":
            conf = context.args[0].lower()
            context.args.pop(0)

            get_set = context.args[0].lower()
            context.args.pop(0)

            # SET a config value
            if get_set == "set":
                # Get value for key
                value = context.args[-1].replace("__", " ")
                context.args.pop(-1)

                # Check value for boolean
                if value.lower() == "true" or value.lower() == "false":
                    value = utl.str2bool(value)

                # Check value for integer
                elif value.isnumeric():
                    value = int(value)

                # Check value for null
                elif value.lower() == "null" or value.lower() == "none":
                    value = None

                try:
                    if plugin == "-":
                        value = self.global_config.set(value, *context.args)
                    else:
                        cfg_file = f"{conf}.json"
                        plg_conf = self.get_cfg_path(plugin=plugin)
                        cfg_path = os.path.join(plg_conf, cfg_file)
                        ConfigManager(cfg_path).set(value, *context.args)
                except Exception as e:
                    logging.error(e)
                    msg = f"{emo.ERROR} {e}"
                    update.message.reply_text(msg)
                    return

                update.message.reply_text(f"{emo.DONE} Config changed")

            # GET a config value
            elif get_set == "get":
                try:
                    if plugin == "-":
                        value = self.global_config.get(*context.args)
                    else:
                        cfg_file = f"{conf}.json"
                        plg_conf = self.get_cfg_path(plugin=plugin)
                        cfg_path = os.path.join(plg_conf, cfg_file)
                        value = ConfigManager(cfg_path).get(*context.args)
                except Exception as e:
                    logging.error(e)
                    msg = f"{emo.ERROR} {e}"
                    update.message.reply_text(msg)
                    return

                update.message.reply_text(value)

            # Wrong syntax
            else:
                update.message.reply_text(
                    text=f"Usage:\n{self.get_usage()}",
                    parse_mode=ParseMode.MARKDOWN)

        # ---- Manage plugins ----
        elif command == "plg":
            try:
                # Start plugin
                if context.args[0].lower() == "add":
                    res = self.add_plugin(plugin)

                # Stop plugin
                elif context.args[0].lower() == "remove":
                    res = self.remove_plugin(plugin)

                # Wrong sub-command
                else:
                    update.message.reply_text(
                        text="Only `add` and `remove` are supported",
                        parse_mode=ParseMode.MARKDOWN)
                    return

                # Reply with message
                if res["success"]:
                    update.message.reply_text(f"{emo.DONE} {res['msg']}")
                else:
                    update.message.reply_text(f"{emo.ERROR} {res['msg']}")
            except Exception as e:
                update.message.reply_text(text=f"{emo.ERROR} {e}")

        else:
            update.message.reply_text(
                text=f"Unknown command `{command}`",
                parse_mode=ParseMode.MARKDOWN)
