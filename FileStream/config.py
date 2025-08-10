from os import environ as env
from dotenv import load_dotenv

# Carga las variables desde .env
load_dotenv()

class Telegram:
    API_ID = int(env.get("API_ID"))
    API_HASH = str(env.get("API_HASH"))
    BOT_TOKEN = str(env.get("BOT_TOKEN"))
    OWNER_ID = int(env.get("OWNER_ID", "7978482443"))
    WORKERS = int(env.get("WORKERS", "6"))  # 6 workers = 6 comandos al mismo tiempo
    DATABASE_URL = str(env.get("DATABASE_URL"))  # En tu caso será redis:// o mongodb://
    UPDATES_CHANNEL = str(env.get("UPDATES_CHANNEL", "Telegram"))
    SESSION_NAME = str(env.get("SESSION_NAME", "FileStream"))
    FORCE_SUB_ID = env.get("FORCE_SUB_ID", None)
    
    FORCE_SUB = str(env.get("FORCE_UPDATES_CHANNEL", "false")).lower() == "true"

    SLEEP_THRESHOLD = int(env.get("SLEEP_THRESHOLD", "60"))
    
    FILE_PIC = env.get("FILE_PIC", "https://graph.org/file/5bb9935be0229adf98b73.jpg")
    START_PIC = env.get("START_PIC", "https://graph.org/file/290af25276fa34fa8f0aa.jpg")
    VERIFY_PIC = env.get("VERIFY_PIC", "https://graph.org/file/736e21cc0efa4d8c2a0e4.jpg")
    
    MULTI_CLIENT = False
    FLOG_CHANNEL = int(env.get("FLOG_CHANNEL", "0")) or None  # Canal para logs de archivos
    ULOG_CHANNEL = int(env.get("ULOG_CHANNEL", "0")) or None  # Canal para logs de usuarios
    
    MODE = env.get("MODE", "primary")
    SECONDARY = MODE.lower() == "secondary"
    
    AUTH_USERS = list(set(int(x) for x in str(env.get("AUTH_USERS", "")).split() if x))

class Server:
    PORT = int(env.get("PORT", "8080"))
    BIND_ADDRESS = str(env.get("BIND_ADDRESS", "0.0.0.0"))
    PING_INTERVAL = int(env.get("PING_INTERVAL", "1200"))
    
    HAS_SSL = str(env.get("HAS_SSL", "0")).lower() in ("1", "true", "t", "yes", "y")
    NO_PORT = str(env.get("NO_PORT", "0")).lower() in ("1", "true", "t", "yes", "y")
    
    FQDN = str(env.get("FQDN", BIND_ADDRESS))
    
    URL = "http{}://{}{}/".format(
        "s" if HAS_SSL else "",
        FQDN,
        "" if NO_PORT else ":" + str(PORT)
    )
