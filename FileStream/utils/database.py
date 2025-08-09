import time
import json
import aioredis
from FileStream.server.exceptions import FIleNotFound

class DatabaseRedis:
    def __init__(self, redis_url, namespace="filestream"):
        self.redis_url = redis_url
        self.redis = None
        self.ns = namespace  # prefijo para evitar colisiones en redis

    async def connect(self):
        self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)

    # ------------------ Usuarios -------------------- #

    def _user_key(self, user_id):
        return f"{self.ns}:user:{user_id}"

    async def new_user(self, user_id):
        return {
            "id": user_id,
            "join_date": time.time(),
            "Links": 0,
        }

    async def add_user(self, user_id):
        user = await self.new_user(user_id)
        await self.redis.set(self._user_key(user_id), json.dumps(user))

    async def get_user(self, user_id):
        data = await self.redis.get(self._user_key(user_id))
        if not data:
            return None
        return json.loads(data)

    async def delete_user(self, user_id):
        await self.redis.delete(self._user_key(user_id))

    async def total_users_count(self):
        keys = await self.redis.keys(f"{self.ns}:user:*")
        return len(keys)

    async def get_all_users(self):
        keys = await self.redis.keys(f"{self.ns}:user:*")
        for key in keys:
            data = await self.redis.get(key)
            if data:
                yield json.loads(data)

    # ------------------ Usuarios baneados -------------------- #

    def _ban_key(self, user_id):
        return f"{self.ns}:ban:{user_id}"

    async def ban_user(self, user_id):
        ban_info = {
            "id": user_id,
            "ban_date": time.time(),
        }
        await self.redis.set(self._ban_key(user_id), json.dumps(ban_info))

    async def unban_user(self, user_id):
        await self.redis.delete(self._ban_key(user_id))

    async def is_user_banned(self, user_id):
        data = await self.redis.get(self._ban_key(user_id))
        return data is not None

    async def total_banned_users_count(self):
        keys = await self.redis.keys(f"{self.ns}:ban:*")
        return len(keys)

    # ------------------ Archivos -------------------- #

    def _file_key(self, file_id):
        return f"{self.ns}:file:{file_id}"

    async def add_file(self, file_info):
        file_info["time"] = time.time()
        old = await self.get_file_by_fileuniqueid(file_info["user_id"], file_info["file_unique_id"])
        if old:
            return old["_id"]
        # guardar nuevo archivo
        file_id = file_info["_id"]
        await self.redis.set(self._file_key(file_id), json.dumps(file_info))
        # actualizar contador links usuario
        await self.count_links(file_info["user_id"], "+")
        return file_id

    async def get_file(self, file_id):
        data = await self.redis.get(self._file_key(file_id))
        if not data:
            raise FIleNotFound
        return json.loads(data)

    async def get_file_by_fileuniqueid(self, user_id, file_unique_id):
        # Redis no soporta búsquedas nativas como Mongo, hacemos iteración simple
        keys = await self.redis.keys(f"{self.ns}:file:*")
        for key in keys:
            data = await self.redis.get(key)
            if not data:
                continue
            file_info = json.loads(data)
            if file_info.get("user_id") == user_id and file_info.get("file_unique_id") == file_unique_id:
                return file_info
        return None

    async def find_files(self, user_id, rang):
        start, end = rang
        keys = await self.redis.keys(f"{self.ns}:file:*")
        user_files = []
        # Filtramos archivos por user_id y ordenamos por tiempo descendente
        for key in keys:
            data = await self.redis.get(key)
            if not data:
                continue
            file_info = json.loads(data)
            if file_info.get("user_id") == user_id:
                user_files.append(file_info)
        user_files.sort(key=lambda x: x.get("time", 0), reverse=True)
        total_files = len(user_files)
        # Slice paginado
        user_files_page = user_files[start-1:end]
        # Para simular cursor en async for, devolvemos lista (cambiar en código si requiere async iterator)
        async def user_files_gen():
            for f in user_files_page:
                yield f
        return user_files_gen(), total_files

    async def total_files(self, user_id=None):
        keys = await self.redis.keys(f"{self.ns}:file:*")
        if user_id is None:
            return len(keys)
        count = 0
        for key in keys:
            data = await self.redis.get(key)
            if not data:
                continue
            file_info = json.loads(data)
            if file_info.get("user_id") == user_id:
                count += 1
        return count

    async def delete_one_file(self, file_id):
        file_info = await self.get_file(file_id)
        await self.redis.delete(self._file_key(file_id))
        await self.count_links(file_info["user_id"], "-")

    async def update_file_ids(self, file_id, file_ids: dict):
        file_info = await self.get_file(file_id)
        file_info["file_ids"] = file_ids
        await self.redis.set(self._file_key(file_id), json.dumps(file_info))

    # ------------------ Contador de links ------------------- #

    async def count_links(self, user_id, operation: str):
        user = await self.get_user(user_id)
        if not user:
            return
        links = user.get("Links", 0)
        if operation == "+":
            links += 1
        elif operation == "-":
            links = max(0, links - 1)
        user["Links"] = links
        await self.redis.set(self._user_key(user_id), json.dumps(user))

    # ------------------ Planes ------------------- #

    async def link_available(self, user_id):
        user = await self.get_user(user_id)
        if not user:
            return False
        plan = user.get("Plan", "Free")
        if plan == "Plus":
            return "Plus"
        elif plan == "Free":
            files = await self.total_files(user_id)
            if files < 11:
                return True
            return False
        return False
