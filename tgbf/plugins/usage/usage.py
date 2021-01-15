import logging

from tgbf.plugin import TGBFPlugin
from telegram.ext import MessageHandler, Filters
from tgbf.web import EndpointAction


class Usage(TGBFPlugin):

    def load(self):
        if not self.table_exists("usage"):
            sql = self.get_resource("create_usage.sql")
            self.execute_sql(sql)

        # Capture all executed commands
        self.add_handler(MessageHandler(
            Filters.command,
            self.usage_callback,
            run_async=True),
            group=1)

        # Add web interface to read usage database
        web_pass = self.config.get("web_password")
        self.add_endpoint(self.name, EndpointAction(self.usage_web, web_pass))

    def usage_callback(self, update, context):
        try:
            chat = update.effective_chat
            user = update.effective_user

            if not chat or not user or not update.message:
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

    def usage_web(self, password):
        sql = self.get_resource("select_usage.sql")
        res = self.execute_sql(sql)

        if not res["success"]:
            return f"ERROR: {res['data']}"
        if not res["data"]:
            return "NO DATA"

        return res["data"]
