import aioredis
import time
import json
from FileStream.server.exceptions import FIleNotFound


class Database:
    def __init__(self, uri, password=None):
        self.uri = uri
        self.password = password
        self.redis = None

    async def connect(self):
        self.redis = await aioredis.from_url(
            self.uri,
            password=self.password,
            encoding="utf-8",
            decode_responses=True
        )

# ---------------------[ USER ]---------------------#
    def new_user(self, id):
        return {
            "id": id,
            "join_date": time.time(),
            "Links": 0
        }

    async def add_user(self, id):
        user_key = f"user:{id}"
        if not await self.redis.exists(user_key):
            await self.redis.hset(user_key, mapping=self.new_user(id))
            await self.redis.sadd("users", id)

    async def get_user(self, id):
        user_key = f"user:{id}"
        return await self.redis.hgetall(user_key)

    async def total_users_count(self):
        return await self.redis.scard("users")

    async def get_all_users(self):
        return await self.redis.smembers("users")

    async def delete_user(self, user_id):
        await self.redis.delete(f"user:{user_id}")
        await self.redis.srem("users", user_id)

# ---------------------[ BAN, UNBAN USER ]---------------------#
    def black_user(self, id):
        return {
            "id": id,
            "ban_date": time.time()
        }

    async def ban_user(self, id):
        await self.redis.hset(f"banned:{id}", mapping=self.black_user(id))
        await self.redis.sadd("banned_users", id)

    async def unban_user(self, id):
        await self.redis.delete(f"banned:{id}")
        await self.redis.srem("banned_users", id)

    async def is_user_banned(self, id):
        return await self.redis.exists(f"banned:{id}") > 0

    async def total_banned_users_count(self):
        return await self.redis.scard("banned_users")

# ---------------------[ FILES ]---------------------#
    async def add_file(self, file_info):
        file_info["time"] = time.time()
        existing = await self.get_file_by_fileuniqueid(file_info["user_id"], file_info["file_unique_id"])
        if existing:
            return existing["file_id"]

        file_id = str(await self.redis.incr("file:id_counter"))
        file_info["file_id"] = file_id

        await self.redis.hset(f"file:{file_id}", mapping={k: json.dumps(v) for k, v in file_info.items()})
        await self.redis.lpush(f"user_files:{file_info['user_id']}", file_id)
        await self.count_links(file_info["user_id"], "+")
        return file_id

    async def find_files(self, user_id, range_tuple):
        start = range_tuple[0] - 1
        end = range_tuple[1] - 1
        file_ids = await self.redis.lrange(f"user_files:{user_id}", start, end)
        total_files = await self.redis.llen(f"user_files:{user_id}")
        files = [await self.get_file(fid) for fid in file_ids]
        return files, total_files

    async def get_file(self, file_id):
        data = await self.redis.hgetall(f"file:{file_id}")
        if not data:
            raise FIleNotFound
        return {k: json.loads(v) for k, v in data.items()}

    async def get_file_by_fileuniqueid(self, user_id, file_unique_id, many=False):
        file_ids = await self.redis.lrange(f"user_files:{user_id}", 0, -1)
        matched_files = []
        for fid in file_ids:
            file_data = await self.get_file(fid)
            if file_data.get("file_unique_id") == file_unique_id:
                if many:
                    matched_files.append(file_data)
                else:
                    return file_data
        return matched_files if many else False

    async def total_files(self, user_id=None):
        if user_id:
            return await self.redis.llen(f"user_files:{user_id}")
        keys = await self.redis.keys("file:*")
        return len(keys)

    async def delete_one_file(self, file_id):
        file_data = await self.get_file(file_id)
        await self.redis.lrem(f"user_files:{file_data['user_id']}", 0, file_id)
        await self.redis.delete(f"file:{file_id}")

    async def update_file_ids(self, file_id, file_ids: dict):
        await self.redis.hset(f"file:{file_id}", "file_ids", json.dumps(file_ids))

# ---------------------[ LINKS COUNT ]---------------------#
    async def count_links(self, user_id, operation: str):
        key = f"user:{user_id}"
        if operation == "-":
            await self.redis.hincrby(key, "Links", -1)
        elif operation == "+":
            await self.redis.hincrby(key, "Links", 1)
