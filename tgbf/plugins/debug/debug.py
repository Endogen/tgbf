import os
import sys
import psutil
import logging
import tgbf.emoji as emo
import tgbf.utils as utl

from tgbf.plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class Debug(TGBFPlugin):

    def load(self):
        self.add_handler(CommandHandler(
            self.name,
            self.debug_callback,
            run_async=True))

    @TGBFPlugin.owner
    @TGBFPlugin.send_typing
    def debug_callback(self, update: Update, context: CallbackContext):
        open_files = psutil.Process().open_files()

        vi = sys.version_info
        v = f"{vi.major}.{vi.minor}.{vi.micro}"

        msg = f"{emo.INFO} PID: {os.getpid()}\n" \
              f"{emo.INFO} Open files: {len(open_files)}\n" \
              f"{emo.INFO} Python: {v}\n" \
              f"{emo.INFO} IP: {utl.get_external_ip()}"

        chat_info = update.effective_chat

        if self.is_private(update.message):
            update.message.reply_text(msg)
        else:
            try:
                self.bot.updater.bot.send_message(
                    update.effective_user.id,
                    f"{msg}\n\n{chat_info}")
            except Exception as e:
                logging.error(f"Could not send debug info: {e}")

        msg = msg.replace("\n", " - ")
        logging.info(f"DEBUG: {msg} - {chat_info}")
