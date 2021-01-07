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

        # Add web interface to read usage database
        self.get_web().add_endpoint(
            endpoint=f"/{self.get_name()}",
            endpoint_name=f"/{self.get_name()}",
            handler=self.usage_web,
            secret=self.get_plugin_config().get("web_password"))

        return self

    # TODO: Only save usage if command exists
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

    def usage_web(self, password):
        sql = self.get_resource("select_usage.sql")
        res = self.execute_sql(sql)

        if not res["success"]:
            return f"ERROR: {res['data']}"
        if not res["data"]:
            return "NO DATA"

        return res["data"]
