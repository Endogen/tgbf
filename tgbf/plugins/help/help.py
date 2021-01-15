from collections import OrderedDict
from tgbf.plugin import TGBFPlugin

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class Help(TGBFPlugin):

    def load(self):
        self.add_handler(CommandHandler(
            self.name,
            self.help_callback,
            run_async=True))

    @TGBFPlugin.send_typing
    def help_callback(self, update: Update, context: CallbackContext):
        categories = OrderedDict()

        for p in self.plugins:
            if p.category and p.description:
                des = f"/{p.handle} - {p.description}"

                if p.category not in categories:
                    categories[p.category] = [des]
                else:
                    categories[p.category].append(des)

        msg = "Available Commands\n\n"

        for category in sorted(categories):
            msg += f"{category}\n"

            for cmd in sorted(categories[category]):
                msg += f"{cmd}\n"

            msg += "\n"

        update.message.reply_text(text=msg, disable_web_page_preview=True)
