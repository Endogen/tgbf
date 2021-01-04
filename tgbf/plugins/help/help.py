from collections import OrderedDict
from tgbf.plugin import TGBFPlugin

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class Help(TGBFPlugin):

    def __enter__(self):
        self.add_handler(CommandHandler(
            self.get_name(),
            self.help_callback,
            run_async=True))

        return self

    @TGBFPlugin.send_typing
    def help_callback(self, update: Update, context: CallbackContext):
        categories = OrderedDict()

        for p in self.get_plugins():
            if p.get_category() and p.get_description():
                des = f"/{p.get_handle()} - {p.get_description()}"

                if p.get_category() not in categories:
                    categories[p.get_category()] = [des]
                else:
                    categories[p.get_category()].append(des)

        msg = "Available Commands\n\n"

        for category in sorted(categories):
            msg += f"{category}\n"

            for cmd in sorted(categories[category]):
                msg += f"{cmd}\n"

            msg += "\n"

        message = update.message.reply_text(
            text=msg,
            disable_web_page_preview=True)

        self.remove_msg(message, also_private=False)
