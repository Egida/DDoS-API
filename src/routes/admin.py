import random
import string
import json
import yaml
import traceback
from starlette.responses import Response
from starlette.requests import Request
from motor.motor_asyncio import AsyncIOMotorClient
from ..utils.db import check_key_in_db

with open("config/config.yml", "r") as f:
    config = yaml.safe_load(f)

mongo = AsyncIOMotorClient(config['config']['mongo_url'])
db = mongo["keys"]

async def admin(request: Request):
    try:
        if (request.headers.get("Authorization") is None or
            request.headers.get("Authorization").replace("Bearer ", "") != config['config']['admin_key']):
            return Response(json.dumps({"success": False, "error": "Invalid admin key."}, indent=4), media_type="application/json", status_code=401)

        action = request.path_params['action']
        user = request.path_params['user']

        if action == "update":
            concurrents = request.query_params.get("concurrents", None)
            time = request.query_params.get("time", None)
        else:
            concurrents = request.query_params.get("concurrents", 1)
            time = request.query_params.get("time", 60)

        if concurrents is None or time is None:
            return Response(json.dumps({"success": False, "error": "You did not insert valid query parameters for updating an user."}, indent=4), media_type="application/json", status_code=400)

        if action == "register":
            return await register(user, int(time), int(concurrents), await check_key_in_db("user", user))
        elif action == "check":
            return await check(await check_key_in_db("user", user))
        elif action == "delete":
            return await delete(user, await check_key_in_db("user", user))
        elif action == "update":
            return await update(user, int(concurrents), int(time), await check_key_in_db("user", user))
    
        return Response(json.dumps({"success": False, "error": "Invalid action."}, indent=4), media_type="application/json", status_code=400)
    except Exception as e:
        print(traceback.format_exc())
        return Response(json.dumps({"success": False, "error": str(e)}, indent=4), media_type="application/json", status_code=400)

async def register(user, time, concurrents, key_check):
    if not key_check:
        key = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(12))
        await db.key.insert_one({"user": user, "key": key, "time": time, "concurrents": concurrents})
        return Response(json.dumps({"success": True, "api_key": key}, indent=4), media_type="application/json", status_code=200)
    else:
        return Response(json.dumps({"success": False, "error": "The specified user already exists."}, indent=4), media_type="application/json", status_code=400)

async def update(user, concurrents, time, key_check):
    if key_check:
        await db.key.update_one(update={"$set": {"time": time, "concurrents": concurrents}}, filter={"user": user})
        return Response(json.dumps({"success": True, "message": "Successfully updated user."}, indent=4), media_type="application/json", status_code=200)
    else:
        return Response(json.dumps({"success": False, "error": "The specified user does not exist."}, indent=4), media_type="application/json", status_code=400)

async def check(key_check):
    if not key_check:
        return Response(json.dumps({"present": False}, indent=4), media_type="application/json", status_code=200)
    else:
        return Response(json.dumps({"present": True, "api_key": key_check["key"]}, indent=4), media_type="application/json", status_code=200)

async def delete(user, key_check):
    if not key_check:
        return Response(json.dumps({"success": False, "error": "The specified user does not exist."}, indent=4), media_type="application/json", status_code=400)
    else:
        await db.key.delete_one({"user": user})
        return Response(json.dumps({"success": True, "message": "Successfully deleted key."}, indent=4), media_type="application/json", status_code=200)
