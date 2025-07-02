from . import (
    start, admin, info, raid_admin,
    backup, fsm_cancel, info_menu,
    guidepage_admin, location_admin, km_lookup, academy
)
from .raid_admin import routers as raid_admin_routers


def register_handlers(dp):
    dp.include_routers(
        backup.router,
        fsm_cancel.router,
        start.router,
        *raid_admin_routers,
        info.router,
        info_menu.router,
        admin.router,
        location_admin.router,
        km_lookup.router,
        guidepage_admin.router,
        academy.router,
    )
