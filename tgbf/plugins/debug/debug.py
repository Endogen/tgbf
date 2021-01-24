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
    @TGBFPlugin.private
    @TGBFPlugin.send_typing
    def debug_callback(self, update: Update, context: CallbackContext):
        open_files = psutil.Process().open_files()

        vi = sys.version_info
        v = f"{vi.major}.{vi.minor}.{vi.micro}"

        msg = f"{emo.INFO} PID: {os.getpid()}\n" \
              f"{emo.INFO} Open files: {len(open_files)}\n" \
              f"{emo.INFO} Python: {v}\n" \
              f"{emo.INFO} IP: {utl.get_external_ip()}"
        update.message.reply_text(msg)
        logging.info(msg.replace("\n", " - "))
