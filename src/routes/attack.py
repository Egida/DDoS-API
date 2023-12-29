import time
import threading
import json
import httpx
import ipaddress
import yaml
import traceback
from starlette.responses import Response
from starlette.requests import Request
from discord_webhook import DiscordEmbed, DiscordWebhook
from ..utils.db import check_key_in_db
from ..utils.ratelimiter import ratelimiter

with open("config/config.yml", "r") as f:
    config = yaml.safe_load(f)

methods = ["TCP", "HTTPS"]

webhook_url = config['config']['webhook']
webhook = DiscordWebhook(url=webhook_url)
slots = []

def slot_append(user):
    slots.append(user)
    time.sleep(20)
    slots.remove(user)
    return

def send_request(url):
    httpx.get(url)
    return

async def attack(request: Request):
    with open("data/blocked_ips.txt", "r") as f:
        blocked_ips = [line.rstrip('\n') for line in f.readlines()]

    try:
        user, key, host, method = (
            request.query_params.get(param, None) for param in
            ["user", "key", "host", "method"]
        )
        port, attack_time = (
            int(request.query_params.get(param, None)) for param in 
            ["port", "time"]
        )
        concurrents = int(request.query_params.get("concurrents", 1))

        if None in [user, key, host, port, attack_time, method]:
            return Response(json.dumps({"success": False, "error": "You did not insert all required query parameters."}, indent=4), status_code=400)

        if '' in [user, key, host, port, attack_time, method]:
            return Response(json.dumps({"success": False, "error": "You did not insert all required query parameters."}, indent=4), status_code=400)
        
        async def check_invalid(key_type, value):
            if not await check_key_in_db(key_type, value):
                return Response(json.dumps({"success": False, "error": f"Invalid {key_type}."}, indent=4), status_code=401)

        await check_invalid("key", key)
        await check_invalid("user", user)

        if await check_key_in_db("user", user) and (await check_key_in_db("user", user))['key'] != key:
            return Response(json.dumps({"success": False, "error": "The key you provided is not assigned to the user you provided."}, indent=4), status_code=401)

        if not host.startswith('http'):
            ipaddress.ip_address(host)

        if method not in methods:
            return Response(json.dumps({"success": False, "error": "Invalid method."}, indent=4), status_code=400)

        if host in blocked_ips:
            return Response(json.dumps({"success": False, "error": "Host is blocked."}, indent=4), status_code=400)
        
        if 'http' in host and method not in ["HTTPS"]:
            return Response(json.dumps({"success": False, "error": "You inserted an URL with a L4 method, which is not allowed."}, indent=4), status_code=400)

        if concurrents > (await check_key_in_db("user", user))['concurrents']:
            return Response(json.dumps({"success": False, "error": f"The concurrent limit for this user is {(await check_key_in_db('user', user))['concurrents']}."}, indent=4), status_code=400)
        
        if attack_time > (await check_key_in_db("user", user))['time']:
            return Response(json.dumps({"success": False, "error": f"The time limit for this user is {(await check_key_in_db('user', user))['time']}."}, indent=4), status_code=400)

        if len(slots) != None and len(slots) > 4:
            return Response(json.dumps({"success": False, "error": "All the slots are being used. Try again later."}, indent=4), status_code=403)

        if not ratelimiter(key):
            return Response(json.dumps({"success": False, "error": "Rate-limited."}, indent=4), status_code=429)

        threading.Thread(target=slot_append, args=[user]).start()

        method_urls = {"TCP": ["https://example.com"], "HTTPS": ["https://example.com"]}

        for _ in range(concurrents):
            for url in set(method_urls[method.lower()]):
                threading.Thread(target=send_request, args=[url]).start()

        embed = DiscordEmbed(title="Example API - Attack Sent", color="2d6bda")
        embed.add_embed_field("User", user, False)
        embed.add_embed_field("Host", host, False)
        embed.add_embed_field("Port", port, False)
        embed.add_embed_field("Time", attack_time, False)
        embed.add_embed_field("Method", method, False)
        embed.add_embed_field("Concurrents", concurrents, False)
        embed.set_footer("example's api ~ the best!")

        webhook.add_embed(embed)
        webhook.execute()

        if "http" in host:
            response_data = {"success": True, "message": "Attack sent.", "info": {"host": host, "port": port, "time": attack_time, "method": method, "concurrents": concurrents}}
        else:
            ip_info = httpx.get(f"http://ip-api.com/json/{host}").json()
            response_data = {"success": True, "message": "Attack sent.", "info": {"host": host, "port": port, "time": attack_time, "method": method, "concurrents": concurrents, "isp": ip_info['isp'], "org": ip_info['org'], "as": ip_info['as'], "timezone": ip_info['timezone']}}

        return Response(json.dumps(response_data, indent=4))
    except ValueError as e:
        print(traceback.format_exc())
        return Response(json.dumps({"success": False, "error": "Invalid host."}, indent=4), status_code=400)
    except Exception as e:
        print(traceback.format_exc())
        return Response(json.dumps({"success": False, "error": str(e)}, indent=4), status_code=500)
