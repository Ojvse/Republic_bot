from .broadcast import router as broadcast_router
from .create import router as create_router
from .delete import router as delete_router
from .journal import router as journal_router
from .pin_fsm_send import router as pin_send_router
from .raid_ui import router as raid_ui_router
from .report import router as report_router
from .ui import router as ui_router

routers = [
    create_router,
    delete_router,
    report_router,
    journal_router,
    ui_router,
    pin_send_router,
    raid_ui_router,
    broadcast_router,
]
