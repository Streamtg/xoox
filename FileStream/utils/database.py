import time
import json
import redis.asyncio as redis
from FileStream.server.exceptions import FIleNotFound

class Database:
    def __init__(self, redis_url):
        # Conexión asíncrona a Redis
        self.redis = redis.from_url(redis_url, decode_responses=True)

    #---------------------[ NEW USER ]---------------------#
    def new_user(self, user_id):
        return {
            "id": user_id,
            "join_date": time.time(),
            "Links": 0,
            "Plan": "Free"  # Default plan
        }

    #---------------------[ ADD USER ]---------------------#
    async def add_user(self, user_id):
        exists = await self.redis.exists(f"user:{user_id}")
        if not exists:
            user = self.new_user(user_id)
            await self.redis.set(f"user:{user_id}", json.dumps(user))

    #---------------------[ GET USER ]---------------------#
    async def get_user(self, user_id):
        data = await self.redis.get(f"user:{user_id}")
        if data:
            return json.loads(data)
        return None

    #---------------------[ TOTAL USERS COUNT ]---------------------#
    async def total_users_count(self):
        keys = await self.redis.keys("user:*")
        return len(keys)

    #---------------------[ GET ALL USERS ]---------------------#
    async def get_all_users(self):
        keys = await self.redis.keys("user:*")
        users = []
        for key in keys:
            data = await self.redis.get(key)
            if data:
                users.append(json.loads(data))
        return users

    #---------------------[ DELETE USER ]---------------------#
    async def delete_user(self, user_id):
        await self.redis.delete(f"user:{user_id}")

    #---------------------[ BAN, UNBAN USER ]---------------------#
    async def ban_user(self, user_id):
        # Ban stored as key "ban:<user_id>"
        await self.redis.set(f"ban:{user_id}", time.time())

    async def unban_user(self, user_id):
        await self.redis.delete(f"ban:{user_id}")

    async def is_user_banned(self, user_id):
        exists = await self.redis.exists(f"ban:{user_id}")
        return exists == 1

    async def total_banned_users_count(self):
        keys = await self.redis.keys("ban:*")
        return len(keys)

    #---------------------[ ADD FILE ]---------------------#
    async def add_file(self, file_info):
        file_id = file_info["_id"]  # Asigna tú mismo el _id antes de llamar
        file_key = f"file:{file_id}"

        exists = await self.redis.exists(file_key)
        if exists:
            return file_id  # Ya existe

        file_info["time"] = time.time()
        await self.increment_links(file_info["user_id"], 1)
        await self.redis.set(file_key, json.dumps(file_info))
        return file_id

    #---------------------[ FIND FILES ]---------------------#
    async def find_files(self, user_id, range_):
        # Redis no es una base de datos con consultas complejas,
        # por lo que guardaremos listas de IDs por usuario para paginar.
        start, end = range_[0]-1, range_[1]
        user_files_key = f"userfiles:{user_id}"
        file_ids = await self.redis.lrange(user_files_key, start, end-1)
        files = []
        for fid in file_ids:
            data = await self.redis.get(f"file:{fid}")
            if data:
                files.append(json.loads(data))
        total_files = await self.redis.llen(user_files_key)
        return files, total_files

    #---------------------[ GET FILE ]---------------------#
    async def get_file(self, file_id):
        data = await self.redis.get(f"file:{file_id}")
        if data:
            return json.loads(data)
        raise FIleNotFound

    #---------------------[ TOTAL FILES ]---------------------#
    async def total_files(self, user_id=None):
        if user_id:
            return await self.redis.llen(f"userfiles:{user_id}")
        else:
            keys = await self.redis.keys("file:*")
            return len(keys)

    #---------------------[ DELETE FILE ]---------------------#
    async def delete_one_file(self, file_id):
        file_key = f"file:{file_id}"
        data = await self.redis.get(file_key)
        if data:
            file_info = json.loads(data)
            await self.redis.delete(file_key)
            # Además, quita este file_id de la lista userfiles
            await self.redis.lrem(f"userfiles:{file_info['user_id']}", 0, file_id)
            await self.increment_links(file_info['user_id'], -1)

    #---------------------[ UPDATE FILE IDS ]---------------------#
    async def update_file_ids(self, file_id, file_ids: dict):
        data = await self.redis.get(f"file:{file_id}")
        if data:
            file_info = json.loads(data)
            file_info["file_ids"] = file_ids
            await self.redis.set(f"file:{file_id}", json.dumps(file_info))

    #---------------------[ LINK AVAILABLE (Plan) ]---------------------#
    async def link_available(self, user_id):
        user = await self.get_user(user_id)
        if not user:
            return False
        if user.get("Plan") == "Plus":
            return "Plus"
        elif user.get("Plan") == "Free":
            files = await self.total_files(user_id)
            if files < 11:
                return True
        return False

    #---------------------[ COUNT LINKS ]---------------------#
    async def increment_links(self, user_id, delta: int):
        # Actualiza el contador Links en el usuario almacenado en Redis
        user = await self.get_user(user_id)
        if user:
            user["Links"] = user.get("Links", 0) + delta
            await self.redis.set(f"user:{user_id}", json.dumps(user))
