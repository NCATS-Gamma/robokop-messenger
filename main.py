from messenger.server import app

# run Flask server (and Swagger UI)
app.run(
    port=8080,
    use_reloader=True
)
