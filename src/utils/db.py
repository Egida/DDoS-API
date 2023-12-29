from motor.motor_asyncio import AsyncIOMotorClient
import yaml

with open("config/config.yml", "r") as f:
    config = yaml.safe_load(f)

mongo = AsyncIOMotorClient(config['config']['mongo_url'])
db = mongo["keys"]

async def check_key_in_db(key_type, key_value):
    return await db.key.find_one({key_type: key_value})
