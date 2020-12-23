import logging

from tgbf.plugin import TGBFPlugin
from telegram.ext import MessageHandler, Filters


class Usage(TGBFPlugin):

    def __enter__(self):
        if not self.table_exists("usage"):
            sql = self.get_resource("create_usage.sql")
            self.execute_sql(sql)

        def save(update, context):
            try:
                c = update.effective_chat

                if c.type.lower() == "private":
                    return

                u = update.effective_user

                if not u:
                    return

                if u.is_bot:
                    return

                sql = self.get_resource("insert_active.sql")
                self.execute_sql(sql, c.id, u.id, "@" + u.username if u.username else u.first_name)
            except Exception as e:
                logging.error(f"ERROR: {e} - UPDATE: {update}")
                self.notify(e)

        # Receive messages if they trigger a command
        self._tgb.dispatcher.add_handler(MessageHandler(Filters.command, save))

        return self

    # Not needed since we use the MessageHandler
    def execute(self, update, context):
        pass
