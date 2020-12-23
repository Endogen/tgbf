import re
import sys
import psutil
import logging
import urllib.request
import tgbf.emoji as emo

from tgbf.plugin import TGBFPlugin
from telegram import Update
from telegram.ext import CallbackContext


class Debug(TGBFPlugin):

    def execute(self, update: Update, context: CallbackContext):
        open_files = psutil.Process().open_files()

        vi = sys.version_info
        v = f"{vi.major}.{vi.minor}.{vi.micro}"

        msg = f"{emo.INFO} Open files: {len(open_files)}\n" \
              f"{emo.INFO} Python: {v}\n" \
              f"{emo.INFO} IP: {self.get_external_ip()}"
        update.message.reply_text(msg)
        logging.info(msg.replace("\n", " - "))

    def get_external_ip(self):
        site = urllib.request.urlopen("http://checkip.dyndns.org/").read()
        grab = re.findall(r"[0-9]+(?:\.[0-9]+){3}", site.decode("utf-8"))
        return grab[0] if grab else "N/A"
