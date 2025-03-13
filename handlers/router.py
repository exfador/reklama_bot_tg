from aiogram import Router

from handlers import common, admin_settings, ad_creation, ad_management


def setup_routers() -> Router:
    """Настраивает и возвращает главный роутер с подключенными дочерними роутерами"""
    router = Router()
    
    router.include_router(common.router)
    router.include_router(admin_settings.router)
    router.include_router(ad_creation.router)
    router.include_router(ad_management.router)
    
    return router 