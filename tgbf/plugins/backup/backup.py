import os
import os.path
import zipfile
import time
import tgbf.emoji as emo
import tgbf.constants as con

from tgbf.plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler


class Backup(TGBFPlugin):

    BACKUP_DIR = "bck"

    def load(self):
        self.add_handler(CommandHandler(
            self.name,
            self.backup_callback,
            pass_args=True,
            run_async=True))

    @TGBFPlugin.owner
    @TGBFPlugin.private
    @TGBFPlugin.send_typing
    def backup_callback(self, update: Update, context: CallbackContext):
        command = ""

        if len(context.args) == 1:
            command = context.args[0].lower().strip()

            if not self.plugin_available(command):
                msg = f"{emo.ERROR} Plugin '{command}' not available"
                update.message.reply_text(msg)
                return

        # List of folders to exclude from backup
        exclude = [con.DIR_LOG, con.DIR_TMP, self.BACKUP_DIR, "__pycache__"]

        # Path to store backup files
        bck_path = os.path.join(con.DIR_SRC, con.DIR_PLG, self.name, self.BACKUP_DIR)

        # Create folder to store backups
        os.makedirs(bck_path, exist_ok=True)

        filename = os.path.join(bck_path, f"{time.strftime('%Y%m%d%H%M%S')}{command}.zip")
        with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            if command:
                base_dir = os.path.join(os.getcwd(), con.DIR_SRC, con.DIR_PLG, command)
            else:
                base_dir = os.getcwd()

            for root, dirs, files in os.walk(base_dir, topdown=True):
                dirs[:] = [d for d in dirs if d not in exclude and not d.startswith(".")]
                for name in dirs:
                    path = os.path.normpath(os.path.join(root, name))
                    write_path = os.path.relpath(path, base_dir)
                    zf.write(path, write_path)
                files[:] = [f for f in files if not f.startswith(".")]
                for name in files:
                    path = os.path.normpath(os.path.join(root, name))
                    write_path = os.path.relpath(path, base_dir)
                    zf.write(path, write_path)

        filepath = os.path.join(os.getcwd(), filename)

        try:
            context.bot.send_document(
                chat_id=update.effective_user.id,
                caption=f"{emo.DONE} Backup created",
                document=open(filepath, 'rb'))
        except Exception as e:
            if os.path.exists(filepath):
                msg = f"{emo.DONE} Backup successfully created but not possible to upload: {e}"
                update.message.reply_text(msg)
                return
