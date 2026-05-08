from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtSql import QSqlQuery


def _new_query():
    return QSqlQuery()


def _normalize_group_kind(group_kind: str) -> tuple[str, str]:
    normalized = str(group_kind or "").strip().lower()
    if normalized == "discount":
        return "discount_group", "discount_percent"
    if normalized == "tax":
        return "tax_group", "tax_percent"
    raise ValueError("Unsupported group kind.")


def _coerce_number(text, label: str) -> float:
    try:
        return max(float(str(text or "").strip() or 0.0), 0.0)
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid number.") from exc


def fetch_active_sales_groups(group_kind: str) -> list[dict]:
    table_name, value_column = _normalize_group_kind(group_kind)
    query = _new_query()
    query.prepare(
        f"""
        SELECT
            id,
            name,
            COALESCE({value_column}, 0),
            COALESCE(fixed_amount, 0),
            COALESCE(apply_on_sale, 1)
        FROM {table_name}
        WHERE COALESCE(status, 'active') = 'active'
        ORDER BY name ASC
        """
    )
    if not query.exec():
        raise Exception(query.lastError().text())

    rows = []
    while query.next():
        rows.append(
            {
                "id": int(query.value(0) or 0),
                "name": str(query.value(1) or "").strip(),
                "percent": float(query.value(2) or 0.0),
                "fixed_amount": float(query.value(3) or 0.0),
                "apply_on_sale": bool(int(query.value(4) or 0)),
            }
        )
    return rows


def fetch_sales_groups(group_kind: str) -> list[dict]:
    table_name, value_column = _normalize_group_kind(group_kind)
    query = _new_query()
    query.prepare(
        f"""
        SELECT
            id,
            name,
            COALESCE({value_column}, 0),
            COALESCE(fixed_amount, 0),
            COALESCE(apply_on_sale, 1),
            COALESCE(status, 'active')
        FROM {table_name}
        ORDER BY
            CASE WHEN COALESCE(status, 'active') = 'active' THEN 0 ELSE 1 END,
            name ASC
        """
    )
    if not query.exec():
        raise Exception(query.lastError().text())

    rows = []
    while query.next():
        rows.append(
            {
                "id": int(query.value(0) or 0),
                "name": str(query.value(1) or "").strip(),
                "percent": float(query.value(2) or 0.0),
                "fixed_amount": float(query.value(3) or 0.0),
                "apply_on_sale": bool(int(query.value(4) or 0)),
                "status": str(query.value(5) or "active").strip(),
            }
        )
    return rows


def fetch_sales_group_detail(group_kind: str, group_id) -> dict | None:
    table_name, value_column = _normalize_group_kind(group_kind)
    query = _new_query()
    query.prepare(
        f"""
        SELECT
            name,
            COALESCE({value_column}, 0),
            COALESCE(fixed_amount, 0),
            COALESCE(apply_on_sale, 1),
            COALESCE(status, 'active')
        FROM {table_name}
        WHERE id = ?
        """
    )
    query.addBindValue(group_id)
    if not query.exec():
        raise Exception(query.lastError().text())
    if not query.next():
        return None

    return {
        "id": int(group_id or 0),
        "name": str(query.value(0) or "").strip(),
        "percent": float(query.value(1) or 0.0),
        "fixed_amount": float(query.value(2) or 0.0),
        "apply_on_sale": bool(int(query.value(3) or 0)),
        "status": str(query.value(4) or "active").strip(),
    }


def save_sales_group(
    *,
    group_kind: str,
    name: str,
    percent_text,
    fixed_amount_text,
    apply_on_sale: bool,
    status: str,
    group_id=None,
) -> int:
    table_name, value_column = _normalize_group_kind(group_kind)
    normalized_name = str(name or "").strip()
    if not normalized_name:
        label = "Discount group name" if group_kind == "discount" else "Tax group name"
        raise ValueError(f"{label} is required.")

    percent_label = "Discount percent" if group_kind == "discount" else "Tax percent"
    percent_value = _coerce_number(percent_text, percent_label)
    fixed_amount = _coerce_number(fixed_amount_text, "Fixed amount")
    normalized_status = str(status or "active").strip() or "active"
    apply_on_sale_value = 1 if apply_on_sale else 0

    query = _new_query()
    if group_id is None:
        query.prepare(
            f"""
            INSERT INTO {table_name} (name, {value_column}, fixed_amount, apply_on_sale, status)
            VALUES (?, ?, ?, ?, ?)
            """
        )
    else:
        query.prepare(
            f"""
            UPDATE {table_name}
            SET name = ?, {value_column} = ?, fixed_amount = ?, apply_on_sale = ?, status = ?
            WHERE id = ?
            """
        )

    query.addBindValue(normalized_name)
    query.addBindValue(percent_value)
    query.addBindValue(fixed_amount)
    query.addBindValue(apply_on_sale_value)
    query.addBindValue(normalized_status)
    if group_id is not None:
        query.addBindValue(group_id)

    if not query.exec():
        raise Exception(query.lastError().text())

    if group_id is not None:
        return int(group_id)
    return int(query.lastInsertId() or 0)
