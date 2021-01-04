import logging

from tgbf.plugin import TGBFPlugin
from telegram.ext import MessageHandler, Filters


class Usage(TGBFPlugin):

    def __enter__(self):
        if not self.table_exists("usage"):
            sql = self.get_resource("create_usage.sql")
            self.execute_sql(sql)

        # Capture all executed commands
        self.add_handler(MessageHandler(
            Filters.command,
            self.usage_callback,
            run_async=True),
            group=1)

        return self

    def usage_callback(self, update, context):
        try:
            chat = update.effective_chat
            user = update.effective_user

            if not chat or not user:
                msg = f"Could not save usage for update: {update}"
                logging.warning(msg)
                return

            sql = self.get_resource("insert_usage.sql")
            self.execute_sql(
                sql,
                user.id,
                user.first_name,
                user.last_name,
                user.username,
                user.language_code,
                chat.id,
                chat.type,
                chat.title,
                update.message.text)
        except Exception as e:
            msg = f"Could not save usage: {e}"
            logging.error(f"{msg} - {update}")
            self.notify(msg)
