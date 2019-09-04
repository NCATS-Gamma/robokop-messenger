"""App entrypoint."""
import os
from messenger.server import app

if __name__ == "__main__":
    app.run(
        port=os.environ['MESSENGER_PORT'],
        use_reloader=True
    )
