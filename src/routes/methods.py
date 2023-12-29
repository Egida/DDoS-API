import json
from starlette.responses import Response

with open("data/methods.json", "r") as f:
    method_list = json.load(f)

async def methods(_):
    return Response(json.dumps(method_list, indent=4), media_type="application/json")