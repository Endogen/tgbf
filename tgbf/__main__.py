import os

from tgbf.start import TGBF


def create_kill_script(filename):
    shebang = "#!/bin/bash"
    command = f"kill -9 {os.getpid()}"

    with open(filename, "w") as f:
        f.truncate(0)
        f.write(f"{shebang}\n\n{command}")


# Create script to kill bot by PID
create_kill_script("kill.sh")

# Entry point for bot
TGBF().start()
