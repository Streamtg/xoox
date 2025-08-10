import os
from dotenv import load_dotenv

load_dotenv()

class Telegram:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    WORKERS = int(os.getenv("WORKERS", 4))
    SLEEP_THRESHOLD = int(os.getenv("SLEEP_THRESHOLD", 60))
    MODE = os.getenv("MODE", "primary")
    SECONDARY = MODE.lower() == "secondary"

    AUTH_USERS = list(set(
        int(x) for x in str(os.getenv("AUTH_USERS", "")).split() if x.isdigit()
    ))

class Server:
    PORT = int(os.getenv("PORT", 8080))
    BIND_ADDRESS = os.getenv("BIND_ADDRESS", "0.0.0.0")
    PING_INTERVAL = int(os.getenv("PING_INTERVAL", 1200))
    HAS_SSL = os.getenv("HAS_SSL", "0").lower() in ("1", "true", "t", "yes", "y")
    NO_PORT = os.getenv("NO_PORT", "0").lower() in ("1", "true", "t", "yes", "y")
    FQDN = os.getenv("FQDN", BIND_ADDRESS)
    URL = "http{}://{}{}/".format(
        "s" if HAS_SSL else "", FQDN, "" if NO_PORT else ":" + str(PORT)
    )
