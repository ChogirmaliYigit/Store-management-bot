from aiogram import Router
from filters import IsBotAdminFilter
from data.config import ADMINS


def setup_routers() -> Router:
    from .users import admin, start, help, main
    from .errors import error_handler
    from .channels import post

    router = Router()

    admin.router.message.filter(IsBotAdminFilter(ADMINS))

    router.include_routers(
        admin.router,
        post.router,
        start.router, help.router, main.router,
        error_handler.router
    )

    return router
