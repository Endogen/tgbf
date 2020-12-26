import os
import logging
import tgbf.emoji as emo
import tgbf.constants as con

from tgbf.plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class Logfile(TGBFPlugin):

    def init(self):
        return CommandHandler(self.get_name(), self.logfile_callback)

    def logfile_callback(self, update: Update, context: CallbackContext):
        base_dir = os.path.abspath(os.getcwd())
        log_file = os.path.join(base_dir, con.DIR_LOG, con.FILE_LOG)

        if os.path.isfile(log_file):
            try:
                file = open(log_file, 'rb')
            except Exception as e:
                logging.error(e)
                self.notify(e)
                file = None
        else:
            file = None

        if file:
            update.message.reply_document(
                caption=f"{emo.DONE} Current Logfile",
                document=file)
        else:
            update.message.reply_text(
                text=f"{emo.ERROR} Not possible to download logfile")
