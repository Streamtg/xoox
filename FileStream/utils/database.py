import time
import json
import aioredis
from bson.objectid import ObjectId
from FileStream.server.exceptions import FIleNotFound

class Database:
    def __init__(self, uri, db_name):
        self.uri = uri
        self.db_name = db_name
        self.redis = None

    async def connect(self):
        self.redis = await aioredis.from_url(self.uri, decode_responses=True)

    # ---------------------[ NEW USER ]--------------------- #
    def new_user(self, id):
        return dict(
            id=id,
            join_date=time.time(),
            Links=0
        )

    async def add_user(self, id):
        user = self.new_user(id)
        await self.redis.hset(f"user:{id}", mapping=user)

    async def get_user(self, id):
        data = await self.redis.hgetall(f"user:{id}")
        return {k: int(v) if v.isdigit() else v for k, v in data.items()} if data else None

    async def total_users_count(self):
        keys = await self.redis.keys("user:*")
        return len(keys)

    async def get_all_users(self):
        keys = await self.redis.keys("user:*")
        for key in keys:
            yield await self.redis.hgetall(key)

    async def delete_user(self, user_id):
        await self.redis.delete(f"user:{user_id}")

    # ---------------------[ BAN, UNBAN USER ]--------------------- #
    async def ban_user(self, id):
        await self.redis.set(f"ban:{id}", time.time())

    async def unban_user(self, id):
        await self.redis.delete(f"ban:{id}")

    async def is_user_banned(self, id):
        return await self.redis.exists(f"ban:{id}") > 0

    async def total_banned_users_count(self):
        keys = await self.redis.keys("ban:*")
        return len(keys)

    # ---------------------[ FILES ]--------------------- #
    async def add_file(self, file_info):
        file_id = str(ObjectId())
        file_info["time"] = time.time()
        await self.redis.set(f"file:{file_id}", json.dumps(file_info))
        await self.count_links(file_info["user_id"], "+")
        return file_id

    async def get_file(self, _id):
        data = await self.redis.get(f"file:{_id}")
        if not data:
            raise FIleNotFound
        return json.loads(data)

    async def delete_one_file(self, _id):
        await self.redis.delete(f"file:{_id}")

    async def update_file_ids(self, _id, file_ids: dict):
        data = await self.get_file(_id)
        data["file_ids"] = file_ids
        await self.redis.set(f"file:{_id}", json.dumps(data))

    async def total_files(self, id=None):
        keys = await self.redis.keys("file:*")
        if not id:
            return len(keys)
        count = 0
        for key in keys:
            data = json.loads(await self.redis.get(key))
            if data.get("user_id") == id:
                count += 1
        return count

    # ---------------------[ PLAN ]--------------------- #
    async def link_available(self, id):
        user = await self.get_user(id)
        if not user:
            return False
        if user.get("Plan") == "Plus":
            return "Plus"
        elif user.get("Plan") == "Free":
            files = await self.total_files(id)
            return files < 11
        return False

    async def count_links(self, id, operation: str):
        if operation == "-":
            await self.redis.hincrby(f"user:{id}", "Links", -1)
        elif operation == "+":
            await self.redis.hincrby(f"user:{id}", "Links", 1)
