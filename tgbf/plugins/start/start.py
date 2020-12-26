from tgbf.plugin import TGBFPlugin
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler


class Start(TGBFPlugin):

    ABOUT_FILE = "about.md"

    def init(self):
        return CommandHandler(self.get_name(), self.start_callback)

    def start_callback(self, update: Update, context: CallbackContext):
        about = self.get_resource(self.ABOUT_FILE)

        update.message.reply_text(
            about,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
