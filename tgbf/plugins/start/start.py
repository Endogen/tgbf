from tgbf.plugin import TGBFPlugin
from telegram import Update, ParseMode
from telegram.ext import CallbackContext


class Start(TGBFPlugin):

    ABOUT_FILE = "about.md"

    def execute(self, update: Update, context: CallbackContext):
        about = self.get_resource(self.ABOUT_FILE)

        update.message.reply_text(
            about,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
