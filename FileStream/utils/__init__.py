from FileStream.config import Telegram
from .database import Database
from .time_format import get_readable_time
from .file_properties import get_name, get_file_ids
from .custom_dl import ByteStreamer
import asyncio

db = Database(Telegram.REDIS_URL, Telegram.SESSION_NAME)

async def init_db():
    await db.connect()

def run_init_db_sync():
    asyncio.run(init_db())
