from .admin import router as admin_router
from .code_dirs import router as code_dirs_router
from .dynamics import router as dynamics_router
from .files import router as files_router
from .reports import router as reports_router

__all__ = [
    "admin_router",
    "dynamics_router",
    "code_dirs_router",
    "files_router",
    "reports_router",
]
