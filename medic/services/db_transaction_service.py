from PySide6.QtSql import QSqlDatabase


def run_in_transaction(
    work_fn,
    *,
    start_error_message="Could not start transaction.",
    commit_error_message="Commit failed.",
):
    db = QSqlDatabase.database()
    if not db.transaction():
        raise RuntimeError(start_error_message)

    try:
        result = work_fn()
    except Exception:
        db.rollback()
        raise

    if not db.commit():
        db.rollback()
        raise RuntimeError(commit_error_message)

    return result
