import json
import re
from calendar import monthrange
from datetime import UTC, date, datetime

from PySide6.QtSql import QSqlQuery


def _new_query():
    return QSqlQuery()


def _table_exists(table_name):
    query = _new_query()
    query.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name=?")
    query.addBindValue(table_name)
    if not query.exec():
        return False
    return bool(query.next())


def _table_columns(table_name):
    columns = set()
    query = _new_query()
    query.prepare(f"PRAGMA table_info({table_name})")
    if not query.exec():
        return columns
    while query.next():
        columns.add(str(query.value(1) or "").strip())
    return columns


def _ensure_column(table_name, column_name, column_sql):
    existing = _table_columns(table_name)
    if column_name in existing:
        return
    query = _new_query()
    if not query.exec(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}"):
        raise Exception(f"Failed to add {column_name} on {table_name}: {query.lastError().text()}")


def _safe_sum(sql, bindings=None):
    query = _new_query()
    query.prepare(sql)
    for value in bindings or []:
        query.addBindValue(value)
    if not query.exec() or not query.next():
        return 0.0
    try:
        return float(query.value(0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def ensure_financial_close_table():
    query = _new_query()
    if not query.exec(
        """
        CREATE TABLE IF NOT EXISTS financial_period_close (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_type TEXT NOT NULL,
            period_label TEXT NOT NULL,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'closed',
            snapshot_json TEXT NOT NULL,
            closed_at TEXT NOT NULL,
            closed_by TEXT,
            notes TEXT,
            reopened_at TEXT,
            reopened_by TEXT,
            reopen_reason TEXT,
            UNIQUE(period_type, period_label)
        )
        """
    ):
        raise Exception(f"Failed to ensure financial_period_close table: {query.lastError().text()}")

    _ensure_column("financial_period_close", "reopen_reason_code", "reopen_reason_code TEXT")

    audit_query = _new_query()
    if not audit_query.exec(
        """
        CREATE TABLE IF NOT EXISTS financial_period_close_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_type TEXT NOT NULL,
            period_label TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_at TEXT NOT NULL,
            event_by TEXT,
            reason_code TEXT,
            reason_text TEXT,
            details_json TEXT
        )
        """
    ):
        raise Exception(f"Failed to ensure financial_period_close_audit table: {audit_query.lastError().text()}")

    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_fin_close_period_status ON financial_period_close(period_type, period_label, status)",
        "CREATE INDEX IF NOT EXISTS idx_fin_close_closed_at ON financial_period_close(closed_at)",
        "CREATE INDEX IF NOT EXISTS idx_fin_close_audit_period_event_at ON financial_period_close_audit(period_type, period_label, event_at)",
        "CREATE INDEX IF NOT EXISTS idx_fin_close_audit_event_type_at ON financial_period_close_audit(event_type, event_at)",
    ]
    for statement in index_statements:
        index_query = _new_query()
        if not index_query.exec(statement):
            raise Exception(f"Failed to ensure financial close index: {index_query.lastError().text()}")


def _sanitize_reason_code(reason_code):
    raw = str(reason_code or "").strip().upper()
    if not raw:
        return "GENERAL"
    normalized = re.sub(r"[^A-Z0-9]+", "_", raw).strip("_")
    return normalized[:24] if normalized else "GENERAL"


def _derive_reason_code(reason, fallback="GENERAL"):
    text = str(reason or "").strip()
    if not text:
        return _sanitize_reason_code(fallback)

    for sep in (":", "-"):
        if sep in text:
            prefix = text.split(sep, 1)[0]
            return _sanitize_reason_code(prefix)

    first_word = text.split()[0] if text.split() else fallback
    return _sanitize_reason_code(first_word)


def _validate_reopen_request(reopened_by, reason):
    actor = str(reopened_by or "").strip()
    if not actor:
        return False, "Reopen user is required."

    note = str(reason or "").strip()
    if not note:
        return False, "Reopen reason is required."
    if len(note) < 10:
        return False, "Reopen reason must be at least 10 characters."
    if len(note.split()) < 2:
        return False, "Reopen reason should include at least two words."

    return True, ""


def _log_financial_close_audit(*, period_type, period_label, event_type, event_by, reason_code="", reason_text="", details=None):
    ensure_financial_close_table()
    payload = details if isinstance(details, dict) else {}
    query = _new_query()
    query.prepare(
        """
        INSERT INTO financial_period_close_audit (
            period_type,
            period_label,
            event_type,
            event_at,
            event_by,
            reason_code,
            reason_text,
            details_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(str(period_type or "").strip().lower())
    query.addBindValue(str(period_label or "").strip())
    query.addBindValue(str(event_type or "").strip().lower())
    query.addBindValue(datetime.now(UTC).isoformat(timespec="seconds"))
    query.addBindValue(str(event_by or "").strip())
    query.addBindValue(_sanitize_reason_code(reason_code))
    query.addBindValue(str(reason_text or "").strip())
    query.addBindValue(json.dumps(payload, ensure_ascii=True))
    query.exec()


def _month_period_bounds(year, month):
    last_day = monthrange(year, month)[1]
    start = date(year, month, 1)
    end = date(year, month, last_day)
    return start, end


def _quarter_period_bounds(year, quarter):
    start_month = ((quarter - 1) * 3) + 1
    end_month = start_month + 2
    start = date(year, start_month, 1)
    end_day = monthrange(year, end_month)[1]
    end = date(year, end_month, end_day)
    return start, end


def build_period_definition(period_type, reference_date):
    normalized_type = str(period_type or "monthly").strip().lower()
    if normalized_type == "quarterly":
        quarter = ((reference_date.month - 1) // 3) + 1
        start, end = _quarter_period_bounds(reference_date.year, quarter)
        label = f"{reference_date.year}-Q{quarter}"
        display_label = f"Q{quarter} {reference_date.year}"
    else:
        start, end = _month_period_bounds(reference_date.year, reference_date.month)
        label = f"{reference_date.year}-{reference_date.month:02d}"
        display_label = start.strftime("%B %Y")
        normalized_type = "monthly"

    return {
        "period_type": normalized_type,
        "period_label": label,
        "display_label": display_label,
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "sort_key": start.isoformat(),
    }


def _shift_month(year, month, delta):
    absolute = (year * 12) + (month - 1) + delta
    new_year = absolute // 12
    new_month = (absolute % 12) + 1
    return new_year, new_month


def _shift_quarter(year, quarter, delta):
    absolute = (year * 4) + (quarter - 1) + delta
    new_year = absolute // 4
    new_quarter = (absolute % 4) + 1
    return new_year, new_quarter


def _parse_month_period_label(period_label):
    text = str(period_label or "").strip()
    match = re.fullmatch(r"(\d{4})-(\d{2})", text)
    if not match:
        return None, None
    year = int(match.group(1))
    month = int(match.group(2))
    if month < 1 or month > 12:
        return None, None
    return year, month


def _parse_quarter_label(quarter_label):
    text = str(quarter_label or "").strip().upper()
    match = re.fullmatch(r"(\d{4})-Q([1-4])", text)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def is_quarter_end_month(period_label):
    _year, month = _parse_month_period_label(period_label)
    return month in {3, 6, 9, 12}


def get_quarter_label_from_month(period_label):
    year, month = _parse_month_period_label(period_label)
    if year is None or month is None:
        return ""
    quarter = ((month - 1) // 3) + 1
    return f"{year}-Q{quarter}"


def _get_quarter_month_labels(quarter_label):
    year, quarter = _parse_quarter_label(quarter_label)
    if year is None or quarter is None:
        return []
    start_month = ((quarter - 1) * 3) + 1
    return [f"{year}-{month:02d}" for month in range(start_month, start_month + 3)]


def is_period_closed(period_type, period_label):
    ensure_financial_close_table()
    query = _new_query()
    query.prepare(
        """
        SELECT 1
        FROM financial_period_close
        WHERE period_type = ?
          AND period_label = ?
          AND status = 'closed'
        LIMIT 1
        """
    )
    query.addBindValue(str(period_type or "").strip().lower())
    query.addBindValue(str(period_label or "").strip())
    if not query.exec():
        return False
    return bool(query.next())


def list_available_periods(period_type="monthly", today=None, lookback_limit=24):
    today = today or date.today()
    normalized_type = str(period_type or "monthly").strip().lower()
    periods = []

    if normalized_type == "quarterly":
        current_quarter = ((today.month - 1) // 3) + 1
        for offset in range(0, int(lookback_limit or 24)):
            year, quarter = _shift_quarter(today.year, current_quarter, -offset)
            month = ((quarter - 1) * 3) + 1
            period = build_period_definition("quarterly", date(year, month, 1))
            if is_period_closed(period["period_type"], period["period_label"]):
                continue
            periods.append(period)
        return periods

    for offset in range(0, int(lookback_limit or 24)):
        year, month = _shift_month(today.year, today.month, -offset)
        period = build_period_definition("monthly", date(year, month, 1))
        if is_period_closed(period["period_type"], period["period_label"]):
            continue
        periods.append(period)

    return periods


def get_month_close_prompt_state(today=None):
    today = today or date.today()
    last_day = monthrange(today.year, today.month)[1]
    if today.day != last_day:
        return {"show": False}

    current_period = build_period_definition("monthly", today)
    if is_period_closed(current_period["period_type"], current_period["period_label"]):
        return {"show": False}

    return {
        "show": True,
        "period_type": current_period["period_type"],
        "period_label": current_period["period_label"],
        "period_start": current_period["period_start"],
        "period_end": current_period["period_end"],
        "display_label": current_period["display_label"],
        "message": (
            f"{current_period['display_label']} is still open. "
            "After closing the day, you should close the month as well."
        ),
    }


def collect_preclose_checks(period_start, period_end):
    checks = []

    if _table_exists("daily_session"):
        open_sessions = _safe_sum(
            "SELECT COUNT(*) FROM daily_session WHERE LOWER(COALESCE(status, '')) = 'open'"
        )
        checks.append(
            {
                "name": "Open cash sessions",
                "severity": "blocking",
                "count": int(open_sessions),
                "action": "Close open sessions before period close.",
                "route": "daily_session_history",
            }
        )

    if _table_exists("batch"):
        negative_batches = _safe_sum(
            "SELECT COUNT(*) FROM batch WHERE COALESCE(quantity_remaining, 0) < 0"
        )
        checks.append(
            {
                "name": "Negative stock batches",
                "severity": "blocking",
                "count": int(negative_batches),
                "action": "Fix stock adjustments before close.",
                "route": "product_list",
            }
        )

    if _table_exists("goods_receipt"):
        pending_grn = _safe_sum(
            """
            SELECT COUNT(*)
            FROM goods_receipt
            WHERE DATE(COALESCE(grn_date, '')) BETWEEN DATE(?) AND DATE(?)
              AND LOWER(COALESCE(status, '')) != 'billed'
            """,
            [period_start, period_end],
        )
        checks.append(
            {
                "name": "Unbilled GRN in period",
                "severity": "review",
                "count": int(pending_grn),
                "action": "Review received stock documents that will carry forward.",
                "route": "grn_list",
            }
        )

    if _table_exists("purchase"):
        unsettled_purchase = _safe_sum(
            """
            SELECT COUNT(*)
            FROM purchase
            WHERE DATE(COALESCE(creation_date, '')) BETWEEN DATE(?) AND DATE(?)
              AND ABS(COALESCE(remaining, 0)) > 0.009
            """,
            [period_start, period_end],
        )
        checks.append(
            {
                "name": "Purchase invoices with remaining balance",
                "severity": "review",
                "count": int(unsettled_purchase),
                "action": "Review supplier balances that will carry forward.",
                "route": "supplier_transactions",
            }
        )

    if _table_exists("sales"):
        unsettled_sales = _safe_sum(
            """
            SELECT COUNT(*)
            FROM sales
            WHERE DATE(COALESCE(date, '')) BETWEEN DATE(?) AND DATE(?)
              AND ABS(COALESCE(remaining, 0)) > 0.009
            """,
            [period_start, period_end],
        )
        checks.append(
            {
                "name": "Sales invoices with remaining balance",
                "severity": "review",
                "count": int(unsettled_sales),
                "action": "Review customer balances that will carry forward.",
                "route": "customer_transactions",
            }
        )

    return checks


def has_blocking_preclose_issues(period_start, period_end):
    checks = collect_preclose_checks(period_start, period_end)
    return any(
        int(check.get("count") or 0) > 0 and str(check.get("severity") or "blocking").strip().lower() == "blocking"
        for check in checks
    )


def build_period_snapshot(period_start, period_end):
    sales_total = _safe_sum(
        "SELECT COALESCE(SUM(COALESCE(total, 0)), 0) FROM sales WHERE DATE(COALESCE(date, '')) BETWEEN DATE(?) AND DATE(?)",
        [period_start, period_end],
    ) if _table_exists("sales") else 0.0

    purchase_total = _safe_sum(
        "SELECT COALESCE(SUM(COALESCE(total, 0)), 0) FROM purchase WHERE DATE(COALESCE(creation_date, '')) BETWEEN DATE(?) AND DATE(?)",
        [period_start, period_end],
    ) if _table_exists("purchase") else 0.0

    expense_total = _safe_sum(
        "SELECT COALESCE(SUM(COALESCE(amount, 0)), 0) FROM expense WHERE DATE(COALESCE(date, '')) BETWEEN DATE(?) AND DATE(?)",
        [period_start, period_end],
    ) if _table_exists("expense") else 0.0

    customer_due = _safe_sum(
        "SELECT COALESCE(SUM(COALESCE(remaining, 0)), 0) FROM sales WHERE ABS(COALESCE(remaining, 0)) > 0.009"
    ) if _table_exists("sales") else 0.0

    supplier_due = _safe_sum(
        "SELECT COALESCE(SUM(COALESCE(remaining, 0)), 0) FROM purchase WHERE ABS(COALESCE(remaining, 0)) > 0.009"
    ) if _table_exists("purchase") else 0.0

    inventory_value = _safe_sum(
        """
        SELECT COALESCE(SUM(COALESCE(quantity_remaining, 0) * COALESCE(unit_cost, 0)), 0)
        FROM batch
        WHERE COALESCE(quantity_remaining, 0) > 0
        """
    ) if _table_exists("batch") else 0.0

    return {
        "period_start": period_start,
        "period_end": period_end,
        "sales_total": round(sales_total, 2),
        "purchase_total": round(purchase_total, 2),
        "expense_total": round(expense_total, 2),
        "customer_due": round(customer_due, 2),
        "supplier_due": round(supplier_due, 2),
        "inventory_value": round(inventory_value, 2),
        "closed_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def close_financial_period(*, period_type, period_label, period_start, period_end, closed_by, notes=""):
    ensure_financial_close_table()
    checks = collect_preclose_checks(period_start, period_end)
    review_items = [
        check
        for check in checks
        if int(check.get("count") or 0) > 0 and str(check.get("severity") or "").strip().lower() == "review"
    ]

    if any(
        int(check.get("count") or 0) > 0 and str(check.get("severity") or "blocking").strip().lower() == "blocking"
        for check in checks
    ):
        return {
            "ok": False,
            "reason": "Blocking pre-close checks found.",
            "checks": checks,
        }

    snapshot = build_period_snapshot(period_start, period_end)
    snapshot["review_items"] = [
        {
            "name": str(check.get("name") or ""),
            "count": int(check.get("count") or 0),
            "action": str(check.get("action") or ""),
            "route": str(check.get("route") or ""),
        }
        for check in review_items
    ]
    snapshot["review_item_count"] = len(review_items)
    query = _new_query()
    query.prepare(
        """
        INSERT OR REPLACE INTO financial_period_close (
            period_type,
            period_label,
            period_start,
            period_end,
            status,
            snapshot_json,
            closed_at,
            closed_by,
            notes,
            reopened_at,
            reopened_by,
            reopen_reason,
            reopen_reason_code
        ) VALUES (?, ?, ?, ?, 'closed', ?, ?, ?, ?, NULL, NULL, NULL, NULL)
        """
    )
    query.addBindValue(str(period_type or "").strip().lower())
    query.addBindValue(str(period_label or "").strip())
    query.addBindValue(str(period_start or "").strip())
    query.addBindValue(str(period_end or "").strip())
    query.addBindValue(json.dumps(snapshot, ensure_ascii=True))
    query.addBindValue(snapshot["closed_at"])
    query.addBindValue(str(closed_by or "").strip())
    query.addBindValue(str(notes or "").strip())

    if not query.exec():
        return {
            "ok": False,
            "reason": query.lastError().text(),
            "checks": checks,
        }

    _log_financial_close_audit(
        period_type=period_type,
        period_label=period_label,
        event_type="closed",
        event_by=closed_by,
        reason_code="PERIOD_CLOSE",
        reason_text=notes,
        details={
            "period_start": period_start,
            "period_end": period_end,
            "snapshot": snapshot,
            "review_items": snapshot.get("review_items") or [],
        },
    )

    return {"ok": True, "snapshot": snapshot}


def reopen_financial_period(*, period_type, period_label, reopened_by, reason, reason_code=None):
    ensure_financial_close_table()
    is_valid, validation_message = _validate_reopen_request(reopened_by, reason)
    if not is_valid:
        return {"ok": False, "reason": validation_message}

    normalized_reason = str(reason or "").strip()
    normalized_actor = str(reopened_by or "").strip()
    normalized_reason_code = _sanitize_reason_code(reason_code or _derive_reason_code(normalized_reason, fallback="REOPEN"))

    now = datetime.now(UTC).isoformat(timespec="seconds")
    query = _new_query()
    query.prepare(
        """
        UPDATE financial_period_close
        SET status = 'reopened',
            reopened_at = ?,
            reopened_by = ?,
            reopen_reason = ?,
            reopen_reason_code = ?
        WHERE period_type = ?
          AND period_label = ?
          AND status = 'closed'
        """
    )
    query.addBindValue(now)
    query.addBindValue(normalized_actor)
    query.addBindValue(normalized_reason)
    query.addBindValue(normalized_reason_code)
    query.addBindValue(str(period_type or "").strip().lower())
    query.addBindValue(str(period_label or "").strip())

    if not query.exec():
        return {"ok": False, "reason": query.lastError().text()}

    if query.numRowsAffected() <= 0:
        return {"ok": False, "reason": "No closed period found to reopen."}

    _log_financial_close_audit(
        period_type=period_type,
        period_label=period_label,
        event_type="reopened",
        event_by=normalized_actor,
        reason_code=normalized_reason_code,
        reason_text=normalized_reason,
        details={},
    )

    return {"ok": True}


def list_recent_period_closures(limit=20):
    ensure_financial_close_table()
    query = _new_query()
    query.prepare(
        """
        SELECT
            period_type,
            period_label,
            period_start,
            period_end,
            status,
            closed_at,
            COALESCE(closed_by, ''),
            COALESCE(notes, ''),
            COALESCE(reopened_at, ''),
            COALESCE(reopened_by, ''),
            COALESCE(reopen_reason, ''),
            COALESCE(reopen_reason_code, ''),
            COALESCE(snapshot_json, '')
        FROM financial_period_close
        ORDER BY closed_at DESC
        LIMIT ?
        """
    )
    query.addBindValue(int(limit or 20))
    if not query.exec():
        return []

    rows = []
    while query.next():
        snapshot_raw = str(query.value(12) or "")
        try:
            snapshot = json.loads(snapshot_raw) if snapshot_raw else {}
        except json.JSONDecodeError:
            snapshot = {}

        rows.append(
            {
                "period_type": str(query.value(0) or ""),
                "period_label": str(query.value(1) or ""),
                "period_start": str(query.value(2) or ""),
                "period_end": str(query.value(3) or ""),
                "status": str(query.value(4) or ""),
                "closed_at": str(query.value(5) or ""),
                "closed_by": str(query.value(6) or ""),
                "notes": str(query.value(7) or ""),
                "reopened_at": str(query.value(8) or ""),
                "reopened_by": str(query.value(9) or ""),
                "reopen_reason": str(query.value(10) or ""),
                "reopen_reason_code": str(query.value(11) or ""),
                "snapshot": snapshot,
            }
        )

    return rows


def get_period_closure(period_type, period_label):
    ensure_financial_close_table()
    query = _new_query()
    query.prepare(
        """
        SELECT
            period_type,
            period_label,
            period_start,
            period_end,
            status,
            closed_at,
            COALESCE(closed_by, ''),
            COALESCE(notes, ''),
            COALESCE(reopened_at, ''),
            COALESCE(reopened_by, ''),
            COALESCE(reopen_reason, ''),
            COALESCE(reopen_reason_code, ''),
            COALESCE(snapshot_json, '')
        FROM financial_period_close
        WHERE period_type = ?
          AND period_label = ?
        LIMIT 1
        """
    )
    query.addBindValue(str(period_type or "").strip().lower())
    query.addBindValue(str(period_label or "").strip())
    if not query.exec() or not query.next():
        return None

    snapshot_raw = str(query.value(12) or "")
    try:
        snapshot = json.loads(snapshot_raw) if snapshot_raw else {}
    except json.JSONDecodeError:
        snapshot = {}

    return {
        "period_type": str(query.value(0) or ""),
        "period_label": str(query.value(1) or ""),
        "period_start": str(query.value(2) or ""),
        "period_end": str(query.value(3) or ""),
        "status": str(query.value(4) or ""),
        "closed_at": str(query.value(5) or ""),
        "closed_by": str(query.value(6) or ""),
        "notes": str(query.value(7) or ""),
        "reopened_at": str(query.value(8) or ""),
        "reopened_by": str(query.value(9) or ""),
        "reopen_reason": str(query.value(10) or ""),
        "reopen_reason_code": str(query.value(11) or ""),
        "snapshot": snapshot,
    }


def list_closed_months_for_quarter(quarter_label):
    month_labels = _get_quarter_month_labels(quarter_label)
    rows = []
    for month_label in month_labels:
        row = get_period_closure("monthly", month_label)
        if not row or str(row.get("status") or "").strip().lower() != "closed":
            return []
        rows.append(row)
    return rows


def is_quarter_summary_available_for_month(period_label):
    quarter_label = get_quarter_label_from_month(period_label)
    if not quarter_label:
        return False
    return len(list_closed_months_for_quarter(quarter_label)) == 3


def get_quarter_summary(quarter_label):
    quarter_text = str(quarter_label or "").strip().upper()
    month_rows = list_closed_months_for_quarter(quarter_text)
    if len(month_rows) != 3:
        return None

    first_row = month_rows[0]
    last_row = month_rows[-1]
    totals = {
        "sales_total": 0.0,
        "purchase_total": 0.0,
        "expense_total": 0.0,
    }
    included_months = []

    for row in month_rows:
        snapshot = row.get("snapshot") if isinstance(row.get("snapshot"), dict) else {}
        included_months.append(str(row.get("period_label") or ""))
        for key in totals:
            try:
                totals[key] += float(snapshot.get(key) or 0.0)
            except (TypeError, ValueError):
                totals[key] += 0.0

    final_snapshot = last_row.get("snapshot") if isinstance(last_row.get("snapshot"), dict) else {}
    display_label = quarter_text.replace("-", " ").replace("Q", "Q")

    return {
        "period_type": "quarterly_summary",
        "quarter_label": quarter_text,
        "display_label": display_label,
        "period_start": str(first_row.get("period_start") or ""),
        "period_end": str(last_row.get("period_end") or ""),
        "included_months": included_months,
        "sales_total": round(totals["sales_total"], 2),
        "purchase_total": round(totals["purchase_total"], 2),
        "expense_total": round(totals["expense_total"], 2),
        "customer_due": round(float(final_snapshot.get("customer_due") or 0.0), 2),
        "supplier_due": round(float(final_snapshot.get("supplier_due") or 0.0), 2),
        "inventory_value": round(float(final_snapshot.get("inventory_value") or 0.0), 2),
        "derived_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def get_quarter_summary_for_month(period_label):
    quarter_label = get_quarter_label_from_month(period_label)
    if not quarter_label:
        return None
    return get_quarter_summary(quarter_label)


def list_financial_close_audit_events(period_type=None, period_label=None, limit=50):
    ensure_financial_close_table()
    clauses = []
    bindings = []

    if period_type:
        clauses.append("period_type = ?")
        bindings.append(str(period_type).strip().lower())
    if period_label:
        clauses.append("period_label = ?")
        bindings.append(str(period_label).strip())

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = _new_query()
    query.prepare(
        f"""
        SELECT
            period_type,
            period_label,
            event_type,
            event_at,
            COALESCE(event_by, ''),
            COALESCE(reason_code, ''),
            COALESCE(reason_text, ''),
            COALESCE(details_json, '')
        FROM financial_period_close_audit
        {where_sql}
        ORDER BY event_at DESC, id DESC
        LIMIT ?
        """
    )
    for value in bindings:
        query.addBindValue(value)
    query.addBindValue(int(limit or 50))
    if not query.exec():
        return []

    rows = []
    while query.next():
        details_raw = str(query.value(7) or "")
        try:
            details = json.loads(details_raw) if details_raw else {}
        except json.JSONDecodeError:
            details = {}
        rows.append(
            {
                "period_type": str(query.value(0) or ""),
                "period_label": str(query.value(1) or ""),
                "event_type": str(query.value(2) or ""),
                "event_at": str(query.value(3) or ""),
                "event_by": str(query.value(4) or ""),
                "reason_code": str(query.value(5) or ""),
                "reason_text": str(query.value(6) or ""),
                "details": details,
            }
        )
    return rows
