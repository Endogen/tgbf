import tgbf.emoji as emo

from tgbf.plugin import TGBFPlugin
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler


class Feedback(TGBFPlugin):

    def load(self):
        if not self.table_exists("feedback"):
            sql = self.get_resource("create_feedback.sql")
            self.execute_sql(sql)

        self.add_handler(CommandHandler(
            self.name,
            self.feedback_callback,
            pass_args=True,
            run_async=True))

    @TGBFPlugin.send_typing
    def feedback_callback(self, update: Update, context: CallbackContext):
        if not context.args:
            update.message.reply_text(
                text=f"Usage:\n{self.get_usage()}",
                parse_mode=ParseMode.MARKDOWN)
            return

        user = update.message.from_user
        if user.username:
            name = f"@{user.username}"
        else:
            name = user.first_name

        feedback = update.message.text.replace(f"/{self.handle} ", "")
        self.notify(f"Feedback from {name}: {feedback}")

        sql = self.get_resource("insert_feedback.sql")
        self.execute_sql(sql, user.id, name, user.username, feedback)

        update.message.reply_text(f"Thanks for letting us know {emo.HEART}")
