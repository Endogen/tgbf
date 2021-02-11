import os
import sys
import time
import logging
import tgbf.emoji as emo

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from tgbf.plugin import TGBFPlugin


class Restart(TGBFPlugin):

    def load(self):
        self.add_handler(CommandHandler(
            self.name,
            self.restart_callback,
            run_async=True))

        chat_id = self.config.get("chat_id")
        mess_id = self.config.get("message_id")

        # If no data saved, don't do anything
        if not mess_id or not chat_id:
            return

        try:
            self.bot.updater.bot.edit_message_text(
                chat_id=chat_id,
                message_id=mess_id,
                text=f"{emo.DONE} Restarting bot...")
        except Exception as e:
            logging.error(str(e))
        finally:
            self.config.remove("chat_id")
            self.config.remove("message_id")

    @TGBFPlugin.owner
    @TGBFPlugin.private
    @TGBFPlugin.send_typing
    def restart_callback(self, update: Update, context: CallbackContext):
        msg = f"{emo.HOURGLASS} Restarting bot..."
        message = update.message.reply_text(msg)

        chat_id = message.chat_id
        mess_id = message.message_id

        self.config.set(chat_id, "chat_id")
        self.config.set(mess_id, "message_id")

        m_name = __spec__.name
        m_name = m_name[:m_name.index(".")]

        time.sleep(1)
        os.execl(sys.executable, sys.executable, '-m', m_name, *sys.argv[1:])
