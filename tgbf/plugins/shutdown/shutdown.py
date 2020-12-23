import threading
import tgbf.emoji as emo

from tgbf.plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext


class Shutdown(TGBFPlugin):

    def execute(self, update: Update, context: CallbackContext):
        msg = f"{emo.GOODBYE} Shutting down..."
        update.message.reply_text(msg)

        threading.Thread(target=self._shutdown_thread).start()

    # TODO: Remove access to protected variable
    def _shutdown_thread(self):
        self._tgb.updater.stop()
        self._tgb.updater.is_idle = False
