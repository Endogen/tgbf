import logging
import threading
import tgbf.emoji as emo

from tgbf.plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class Shutdown(TGBFPlugin):

    def load(self):
        self.add_handler(CommandHandler(
            self.name,
            self.shutdown_callback,
            run_async=True))

    @TGBFPlugin.owner
    @TGBFPlugin.private
    @TGBFPlugin.send_typing
    def shutdown_callback(self, update: Update, context: CallbackContext):
        msg = f"{emo.GOODBYE} Shutting down..."
        update.message.reply_text(msg)
        logging.info(msg)

        threading.Thread(target=self._shutdown_thread).start()

    def _shutdown_thread(self):
        self.bot.updater.stop()
        self.bot.updater.is_idle = False
