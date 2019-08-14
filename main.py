import os
from messenger.server import app

# run Flask server (and Swagger UI)
app.run(
    port=os.environ['MESSENGER_PORT'],
    use_reloader=True
)
