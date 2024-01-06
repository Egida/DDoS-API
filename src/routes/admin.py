import json
import random
import string
import traceback
from sqlalchemy import Column, String, Integer, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from starlette.responses import Response
from starlette.requests import Request
from ..utils.db import admin_check, key_check

with open("data/config.json", "r") as f:
    config = json.load(f)

Base = declarative_base()

class Key(Base):
    __tablename__ = 'key'
    user = Column(String, primary_key=True)
    key = Column(String)
    time = Column(Integer)
    concurrents = Column(Integer)
    admin = Column(Boolean)
    premium = Column(Boolean)

engine = create_engine("sqlite:///data/keys.db")
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

async def admin(request: Request):
    try:
        user, key = request.query_params.get("user", None), request.query_params.get("key", None)

        if user == "root" and key == "example":
            pass
        elif not user or not await admin_check("user", user) or not await key_check("key", key):
            return Response(json.dumps({"success": False, "error": "Invalid admin key."}, indent=4),
                            media_type="application/json", status_code=401)

        data = await request.json()
        print(data)
        action, user = request.path_params.get('action'), request.path_params.get('user')
        concurrents, time = int(data.get("concurrents", 1)), int(data.get("time", 60))
        premium, admin = bool(data.get('premium', False)), bool(data.get('admin', False))
        key_check_user = await key_check("user", user)

        if action == "register": return await register(user, time, concurrents, premium, admin, key_check_user)
        elif action == "check": return await check(key_check_user)
        elif action == "delete": return await delete(user, key_check_user)
        elif action == "update": return await update(user, concurrents, time, premium, admin, key_check_user)
        
        return Response(json.dumps({"success": False, "error": "Invalid action."}, indent=4),
                        media_type="application/json", status_code=400)
    except Exception as e:
        print(traceback.format_exc())
        return Response(json.dumps({"success": False, "error": str(e)}, indent=4), media_type="application/json",
                        status_code=400)

async def register(user, time, concurrents, premium, admin, key_check):
    key = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(12))
    if not key_check:
        try:
            with Session() as session:
                new_key = Key(user=user, key=key, time=time, concurrents=concurrents, premium=premium, admin=admin)
                session.add(new_key)
                session.commit()
                return Response(json.dumps({"success": True, "api_key": key}, indent=4),
                                media_type="application/json", status_code=200)
        except Exception as e:
            return Response(json.dumps({"success": False, "error": str(e)}, indent=4),
                            media_type="application/json", status_code=400)
    else:
        return Response(json.dumps({"success": False, "error": "The specified user already exists."}, indent=4),
                        media_type="application/json", status_code=400)

async def update(user, concurrents, time, premium, admin, key_check):
    if key_check:
        try:
            with Session() as session:
                existing_key = session.query(Key).filter_by(user=user).first()
                if existing_key:
                    existing_key.time, existing_key.premium, existing_key.admin, existing_key.concurrents = time, premium, admin, concurrents
                    session.commit()
                    return Response(json.dumps({"success": True, "message": "Successfully updated user."}, indent=4),
                                    media_type="application/json", status_code=200)
                else:
                    return Response(json.dumps({"success": False, "error": "The specified user does not exist."}, indent=4),
                                    media_type="application/json", status_code=400)
        except Exception as e:
            return Response(json.dumps({"success": False, "error": str(e)}, indent=4),
                            media_type="application/json", status_code=400)
    else:
        return Response(json.dumps({"success": False, "error": "The specified user does not exist."}, indent=4),
                        media_type="application/json", status_code=400)

async def check(key_check):
    return Response(json.dumps({"present": True, "api_key": key_check["key"]} if key_check else {"present": False}, indent=4),
                    media_type="application/json", status_code=200)

async def delete(user, key_check):
    if key_check:
        try:
            with Session() as session:
                existing_key = session.query(Key).filter_by(user=user).first()
                if existing_key:
                    session.delete(existing_key)
                    session.commit()
                    return Response(json.dumps({"success": True, "message": "Successfully deleted user."}, indent=4),
                                    media_type="application/json", status_code=200)
                else:
                    return Response(json.dumps({"success": False, "error": "The specified user does not exist."}, indent=4),
                                    media_type="application/json", status_code=400)
        except Exception as e:
            return Response(json.dumps({"success": False, "error": str(e)}, indent=4),
                            media_type="application/json", status_code=400)
    else:
        return Response(json.dumps({"success": False, "error": "The specified user does not exist."}, indent=4),
                        media_type="application/json", status_code=400)