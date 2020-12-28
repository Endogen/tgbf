import threading
import tgbf.emoji as emo

from tgbf.plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class Shutdown(TGBFPlugin):

    def __enter__(self):
        self.add_handler(CommandHandler(
            self.get_name(),
            self.shutdown_callback,
            run_async=True))

        return self

    def shutdown_callback(self, update: Update, context: CallbackContext):
        msg = f"{emo.GOODBYE} Shutting down..."
        update.message.reply_text(msg)

        threading.Thread(target=self._shutdown_thread).start()

    # TODO: Remove access to protected variable
    def _shutdown_thread(self):
        self._tgb.updater.stop()
        self._tgb.updater.is_idle = False
