from starlette.responses import PlainTextResponse

async def home(_):
    return PlainTextResponse("Example API")