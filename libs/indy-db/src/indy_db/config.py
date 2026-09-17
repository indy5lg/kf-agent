import os

DATABASE_URL = os.environ["DATABASE_URL"]
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", 604800))
