import logging

from PySide6.QtWidgets import QMessageBox

from medic.utilities.session_service import SessionErrorCode, check_active_session
from medic.utilities.app_messagebox import AppMessageBox


logger = logging.getLogger(__name__)


def require_open_session(parent_widget):
    """
    UI adapter around session_service that enforces an open session and renders
    user-facing messages for failures.
    """
    result = check_active_session(strict=True)

    if result.ok:
        return True

    logger.warning(
        "Session gate denied",
        extra={
            "session_code": result.code,
            "session_id": result.session_id,
            "session_error": result.error_text,
        },
    )

    if result.code == SessionErrorCode.DB_ERROR:
        AppMessageBox.critical(
            parent_widget,
            "Database Error",
            f"Error checking session: {result.error_text}",
        )
        return False

    if result.code == SessionErrorCode.MULTIPLE_OPEN_SESSIONS:
        AppMessageBox.critical(
            parent_widget,
            "Session Data Error",
            "Multiple open daily sessions were found.\n\n"
            "Please close duplicate sessions before creating transactions.",
        )
        return False

    AppMessageBox.warning(
        parent_widget,
        "No Active Session",
        "You must open a daily session before creating any transactions.\n\n"
        "Please go to Dashboard -> Daily Sessions and click 'Open Day' first.",
    )
    return False
