from starlette.applications import Starlette
from starlette.routing import Route

from .routes.admin import admin
from .routes.attack import attack
from .routes.home import home
from .routes.methods import methods

app = Starlette(
    debug=True,
    routes=[
        Route('/admin/{action:str}/{user:str}', admin, methods=["POST"]),
        Route('/api/attack', attack, methods=["GET"]),
        Route('/', home, methods=["GET"]),
        Route('/methods', methods, methods=["GET"])
    ]
)