def is_numeric(string):
    """ Also accepts '.' in the string. Function 'isnumeric()' doesn't """
    try:
        float(string)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(string)
        return True
    except (TypeError, ValueError):
        pass

    return False


def esc_md(text):
    import re

    rep = {"_": "\\_", "*": "\\*", "[": "\\[", "`": "\\`"}
    rep = dict((re.escape(k), v) for k, v in rep.items())
    pattern = re.compile("|".join(rep.keys()))

    return pattern.sub(lambda m: rep[re.escape(m.group(0))], text)


def build_menu(buttons, n_cols=1, header_buttons=None, footer_buttons=None):
    """ Build button-menu for Telegram """
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]

    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)

    return menu


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


def split_msg(msg, max_len=None, split_char="\n", only_one=False):
    """ Restrict message length to max characters as defined by Telegram """
    if not max_len:
        import t2xbot.constants as con
        max_len = con.MAX_TG_MSG_LEN

    if only_one:
        return [msg[:max_len][:msg[:max_len].rfind(split_char)]]

    remaining = msg
    messages = list()
    while len(remaining) > max_len:
        split_at = remaining[:max_len].rfind(split_char)
        message = remaining[:max_len][:split_at]
        messages.append(message)
        remaining = remaining[len(message):]
    else:
        messages.append(remaining)

    return messages


def encode_url(trxid):
    import urllib.parse as ul
    return ul.quote_plus(trxid)


def id(length=8):
    import string, random
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(random.choices(alphabet, k=length))


def to_unix_time(date_time, millis=False):
    from datetime import datetime
    seconds = (date_time - datetime(1970, 1, 1)).total_seconds()
    return int(seconds * 1000 if millis else seconds)


def from_unix_time(seconds, millis=False):
    from datetime import datetime
    return datetime.utcfromtimestamp(seconds / 1000 if millis else seconds)


def get_external_ip():
    import urllib.request, re
    site = urllib.request.urlopen("http://checkip.dyndns.org/").read()
    grab = re.findall(r"[0-9]+(?:\.[0-9]+){3}", site.decode("utf-8"))
    return grab[0] if grab else None
