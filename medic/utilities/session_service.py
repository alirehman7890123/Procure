from dataclasses import dataclass
import logging

from typing import Optional

from PySide6.QtSql import QSqlQuery


logger = logging.getLogger(__name__)


class SessionErrorCode:
    OK = "ok"
    NO_OPEN_SESSION = "no_open_session"
    MULTIPLE_OPEN_SESSIONS = "multiple_open_sessions"
    DB_ERROR = "db_error"
    INVALID_SESSION_ROW = "invalid_session_row"


@dataclass
class SessionCheckResult:
    ok: bool
    code: str
    session_id: Optional[int] = None
    message: str = ""
    error_text: str = ""


@dataclass
class ActiveSessionRecord:
    id: int
    session_date: str = ""
    opened_at: str = ""
    status: str = "open"


def _build_open_session_query(limit: int = 2) -> QSqlQuery:
    query = QSqlQuery()
    query.prepare(
        """
        SELECT id
        FROM daily_session
        WHERE status = 'open'
        ORDER BY id DESC
        LIMIT ?
        """
    )
    query.addBindValue(limit)
    return query


def check_active_session(strict: bool = True) -> SessionCheckResult:
    """
    Resolve active session state.

    strict=True:
      - multiple open sessions is considered an error.
    strict=False:
      - latest open session is returned even if duplicates exist.
    """
    logger.debug("Session check started", extra={"strict": strict})

    query = _build_open_session_query(limit=2)

    if not query.exec():
        logger.error("Session check DB error", extra={"strict": strict, "error": query.lastError().text()})
        return SessionCheckResult(
            ok=False,
            code=SessionErrorCode.DB_ERROR,
            message="Error fetching active session.",
            error_text=query.lastError().text(),
        )

    ids = []
    while query.next():
        raw_id = query.value(0)
        try:
            ids.append(int(raw_id))
        except (TypeError, ValueError):
            logger.error("Session check invalid row", extra={"raw_id": raw_id})
            return SessionCheckResult(
                ok=False,
                code=SessionErrorCode.INVALID_SESSION_ROW,
                message="Invalid active session row.",
                error_text=f"Invalid session id value: {raw_id}",
            )

    if not ids:
        logger.info("Session check no open session", extra={"strict": strict})
        return SessionCheckResult(
            ok=False,
            code=SessionErrorCode.NO_OPEN_SESSION,
            message="No active session found.",
        )

    latest_session_id = ids[0]

    if len(ids) > 1 and strict:
        logger.warning("Session check multiple open sessions", extra={"strict": strict, "latest_session_id": latest_session_id})
        return SessionCheckResult(
            ok=False,
            code=SessionErrorCode.MULTIPLE_OPEN_SESSIONS,
            session_id=latest_session_id,
            message="Multiple open sessions found; fix daily session state before continuing.",
        )

    logger.debug("Session check ok", extra={"strict": strict, "session_id": latest_session_id})
    return SessionCheckResult(
        ok=True,
        code=SessionErrorCode.OK,
        session_id=latest_session_id,
    )


def has_active_session(strict: bool = True) -> bool:
    return check_active_session(strict=strict).ok


def get_active_session_id(strict: bool = False) -> Optional[int]:
    """
    strict=False preserves legacy behavior by selecting latest open session.
    strict=True fails on duplicate open sessions.
    """
    result = check_active_session(strict=strict)
    if result.ok:
        return result.session_id
    return None


def get_active_session(strict: bool = True) -> Optional[dict]:
    """
    Return a minimal active session payload for callers that need more than ID.
    """
    result = check_active_session(strict=strict)
    if not result.ok:
        return None

    return {
        "id": result.session_id,
        "status": "open",
    }


def get_active_session_record(strict: bool = True) -> Optional[ActiveSessionRecord]:
    """
    Resolve active session record details for callers that need more context.
    """
    session_id = get_active_session_id(strict=strict)
    if session_id is None:
        return None

    query = QSqlQuery()
    query.prepare(
        """
        SELECT id, COALESCE(session_date, ''), COALESCE(opened_at, ''), COALESCE(status, 'open')
        FROM daily_session
        WHERE id = ?
        LIMIT 1
        """
    )
    query.addBindValue(int(session_id))

    if not query.exec() or not query.next():
        logger.warning("Active session record lookup failed", extra={"session_id": session_id})
        return None

    return ActiveSessionRecord(
        id=int(query.value(0)),
        session_date=str(query.value(1) or ""),
        opened_at=str(query.value(2) or ""),
        status=str(query.value(3) or "open"),
    )


def assert_active_session(strict: bool = True) -> int:
    """
    Hard-gate API: return active session ID or raise RuntimeError with code context.
    """
    result = check_active_session(strict=strict)
    if result.ok and result.session_id is not None:
        return int(result.session_id)

    raise RuntimeError(f"session_gate_failed:{result.code}:{result.message}")
