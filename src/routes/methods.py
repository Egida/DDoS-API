import json
from starlette.responses import Response

with open("data/funnel.json", "r") as f:
    info = json.load(f)

async def methods(_):
    return Response(
        json.dumps({"methods": [{"method": method, "description": info['methods'][method]['description'], "type": info['methods'][method]['type']} for method in info['methods']]}, indent=4),
        media_type="application/json"
    )
