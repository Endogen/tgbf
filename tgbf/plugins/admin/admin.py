import os
import logging
import tgbf.utils as utl
import tgbf.emoji as emo

from telegram import ParseMode, Update
from telegram.ext import CallbackContext, CommandHandler
from tgbf.config import ConfigManager
from tgbf.plugin import TGBFPlugin


# TODO: List all plugins, not only command-based plugins. Allow to disable / enable them via buttons
class Admin(TGBFPlugin):

    def load(self):
        self.add_handler(CommandHandler(
            self.name,
            self.admin_callback,
            run_async=True))

    @TGBFPlugin.owner
    @TGBFPlugin.private
    @TGBFPlugin.send_typing
    def admin_callback(self, update: Update, context: CallbackContext):
        if not len(context.args) >= 3:
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
                    emoji = '\n'.join(str(s) for s in res["data"])
                else:
                    emoji = f"{emo.INFO} No data returned"
            else:
                emoji = f"{emo.ERROR} {res['data']}"

            update.message.reply_text(emoji)

        # ---- Change configuration (global or plugin) ----
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
                        self.global_config.set(value, *context.args)
                    else:
                        self.get_cfg_manager(plugin=plugin).set(value, *context.args)
                except Exception as e:
                    logging.error(e)
                    emoji = f"{emo.ERROR} {e}"
                    update.message.reply_text(emoji)
                    return

                update.message.reply_text(f"{emo.DONE} Config changed")

            # GET a config value
            elif get_set == "get":
                try:
                    if plugin == "-":
                        value = self.global_config.get(*context.args)
                    else:
                        cfg_file = conf if conf.endswith("json") else f"{conf}.json"
                        plg_conf = self.get_cfg_path(plugin=plugin)
                        cfg_path = os.path.join(plg_conf, cfg_file)
                        value = ConfigManager(cfg_path).get(*context.args)
                except Exception as e:
                    logging.error(e)
                    emoji = f"{emo.ERROR} {e}"
                    update.message.reply_text(emoji)
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
                # Enable plugin
                if context.args[0].lower() == "enable":
                    res = self.bot.enable_plugin(plugin)

                # Disable plugin
                elif context.args[0].lower() == "disable":
                    res = self.bot.disable_plugin(plugin)

                # Wrong sub-command
                else:
                    update.message.reply_text(
                        text=f"{emo.ERROR} Use `enable` or `disable`",
                        parse_mode=ParseMode.MARKDOWN)
                    return

                emoji = f"{emo.DONE} " if res[0] else f"{emo.ERROR} "
                update.message.reply_text(emoji + res[1])
            except Exception as e:
                update.message.reply_text(text=f"{emo.ERROR} {repr(e)}")
                logging.error(repr(e))

        else:
            update.message.reply_text(
                text=f"Unknown command `{command}`",
                parse_mode=ParseMode.MARKDOWN)
