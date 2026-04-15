import re


def _new_query():
    from PySide6.QtSql import QSqlQuery

    return QSqlQuery()


def normalize_po_number(value):
    po_number = str(value or "").strip().upper()
    if not po_number:
        return ""
    if not re.fullmatch(r"PO-\d+", po_number):
        raise ValueError("PO number must follow format PO-<digits>, e.g. PO-1001.")
    return po_number


def build_purchase_order_header_payload(
    *,
    po_number,
    supplier_id,
    po_date,
    expected_delivery_date,
    total_value,
    notes,
    session_id,
    status="draft",
):
    return {
        "po_number": str(po_number or "").strip().upper(),
        "supplier": supplier_id,
        "po_date": po_date,
        "expected_delivery_date": expected_delivery_date,
        "status": str(status or "draft").strip() or "draft",
        "total_value": float(total_value or 0.0),
        "notes": str(notes or "").strip(),
        "session_id": session_id,
    }


def normalize_purchase_order_line_row(*, product_id, qty, unit_price, row_number=None):
    row_label = f"row {row_number}" if row_number is not None else "purchase order row"

    try:
        normalized_product_id = int(product_id)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid product on {row_label}.")

    try:
        normalized_qty = int(qty)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid qty on {row_label}.")

    try:
        normalized_unit_price = float(unit_price)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid unit price on {row_label}.")

    if normalized_product_id <= 0:
        raise ValueError(f"Invalid product on {row_label}.")
    if normalized_qty <= 0:
        raise ValueError(f"Qty must be greater than zero on {row_label}.")
    if normalized_unit_price < 0:
        raise ValueError(f"Unit price cannot be negative on {row_label}.")

    return {
        "product": normalized_product_id,
        "qty_ordered": normalized_qty,
        "unit_price": normalized_unit_price,
        "total_price": round(normalized_qty * normalized_unit_price, 2),
    }


def compute_reorder_suggestion(*, suggested_units, pack_size, reorder_level):
    try:
        normalized_units = int(float(suggested_units or 0))
    except (TypeError, ValueError):
        normalized_units = 0

    try:
        normalized_pack_size = max(1, int(float(pack_size or 1)))
    except (TypeError, ValueError):
        normalized_pack_size = 1

    try:
        normalized_reorder_level = max(0, int(float(reorder_level or 0)))
    except (TypeError, ValueError):
        normalized_reorder_level = 0

    if normalized_units > 0:
        suggested_qty = max(1, (normalized_units + normalized_pack_size - 1) // normalized_pack_size)
        return {
            "suggested_qty": suggested_qty,
            "suggested_units": normalized_units,
            "average_per_day": normalized_units / 30.0,
            "source": "sales_30d",
        }

    if normalized_reorder_level > 0:
        return {
            "suggested_qty": normalized_reorder_level,
            "suggested_units": 0,
            "average_per_day": 0.0,
            "source": "reorder_level",
        }

    return {
        "suggested_qty": 0,
        "suggested_units": 0,
        "average_per_day": 0.0,
        "source": "none",
    }


def build_low_stock_product_row(
    *,
    product_id,
    product_name,
    manufacturer_name,
    stock_qty,
    reorder_level,
    last_cost,
):
    try:
        normalized_stock_qty = int(float(stock_qty or 0))
    except (TypeError, ValueError):
        normalized_stock_qty = 0
    try:
        normalized_reorder_level = int(float(reorder_level or 0))
    except (TypeError, ValueError):
        normalized_reorder_level = 0
    try:
        normalized_last_cost = float(last_cost or 0.0)
    except (TypeError, ValueError):
        normalized_last_cost = 0.0

    suggested_qty = max(normalized_reorder_level - normalized_stock_qty, 1) if normalized_reorder_level > normalized_stock_qty else 1

    if normalized_stock_qty <= 0:
        status_reason = "Out of stock"
    elif normalized_reorder_level > 0:
        status_reason = "Below reorder level"
    else:
        status_reason = "Low stock"

    return {
        "product_id": product_id,
        "product_name": str(product_name or "").strip(),
        "manufacturer_name": str(manufacturer_name or "").strip() or "Unassigned Manufacturer",
        "stock_qty": normalized_stock_qty,
        "reorder_level": normalized_reorder_level,
        "suggested_qty": suggested_qty,
        "last_cost": normalized_last_cost,
        "status_reason": status_reason,
    }


def fetch_last_purchase_order_cost(product_id):
    query = _new_query()
    query.prepare(
        """
        SELECT rate
        FROM purchaseitem
        WHERE product = ?
        ORDER BY id DESC
        LIMIT 1
        """
    )
    query.addBindValue(product_id)
    if query.exec() and query.next():
        try:
            return float(query.value(0) or 0.0), "invoice"
        except (TypeError, ValueError):
            pass

    query.prepare(
        """
        SELECT unit_price
        FROM purchase_order_line
        WHERE product = ?
        ORDER BY id DESC
        LIMIT 1
        """
    )
    query.addBindValue(product_id)
    if query.exec() and query.next():
        try:
            return float(query.value(0) or 0.0), "po"
        except (TypeError, ValueError):
            pass

    return None, None


def fetch_product_reorder_level(product_id):
    query = _new_query()
    query.prepare(
        """
        SELECT COALESCE(MAX(COALESCE(reorder_level, 0)), 0)
        FROM price_pack
        WHERE product_id = ?
        """
    )
    query.addBindValue(product_id)
    if query.exec() and query.next():
        try:
            return int(float(query.value(0) or 0))
        except (TypeError, ValueError):
            return 0
    return 0


def fetch_pack_size(product_id):
    query = _new_query()
    query.prepare(
        """
        SELECT COALESCE(pack_size, 1)
        FROM price_pack
        WHERE product_id = ?
        ORDER BY is_default DESC, id ASC
        LIMIT 1
        """
    )
    query.addBindValue(product_id)
    if query.exec() and query.next():
        try:
            return max(1, int(float(query.value(0) or 1)))
        except (TypeError, ValueError):
            return 1
    return 1


def fetch_recent_sales_units(product_id):
    query = _new_query()
    query.prepare(
        """
        SELECT COALESCE(SUM(COALESCE(si.qty_sold, 0)), 0)
        FROM salesitem si
        JOIN sales s ON s.id = si.sales_id
        WHERE si.product_id = ?
          AND DATE(s.creation_date) >= DATE('now', '-30 days')
        """
    )
    query.addBindValue(product_id)
    if not query.exec():
        raise Exception(query.lastError().text())
    if query.next():
        try:
            return int(float(query.value(0) or 0))
        except (TypeError, ValueError):
            return 0
    return 0


def fetch_low_stock_products():
    query = _new_query()
    query.prepare(
        """
        SELECT
            p.id,
            COALESCE(p.display_name, '') AS product_name,
            COALESCE(m.name, '') AS manufacturer_name,
            COALESCE(bs.total_stock, 0) AS stock_qty,
            COALESCE(pp.reorder_level, 0) AS reorder_level
        FROM product p
        LEFT JOIN manufacturer m ON p.manufacturer_id = m.id
        LEFT JOIN (
            SELECT product_id, COALESCE(SUM(quantity_remaining), 0) AS total_stock
            FROM batch
            GROUP BY product_id
        ) bs ON bs.product_id = p.id
        LEFT JOIN (
            SELECT product_id, MAX(COALESCE(reorder_level, 0)) AS reorder_level
            FROM price_pack
            GROUP BY product_id
        ) pp ON pp.product_id = p.id
        WHERE p.status = 'used'
          AND (
                COALESCE(bs.total_stock, 0) <= COALESCE(pp.reorder_level, 0)
                OR COALESCE(bs.total_stock, 0) <= 0
              )
        ORDER BY COALESCE(m.name, 'Unassigned Manufacturer') ASC, COALESCE(p.display_name, '') ASC
        """
    )
    if not query.exec():
        raise Exception(query.lastError().text())

    rows = []
    while query.next():
        product_id = query.value(0)
        last_cost, _ = fetch_last_purchase_order_cost(product_id)
        rows.append(
            build_low_stock_product_row(
                product_id=product_id,
                product_name=query.value(1),
                manufacturer_name=query.value(2),
                stock_qty=query.value(3),
                reorder_level=query.value(4),
                last_cost=last_cost,
            )
        )
    return rows


def fetch_next_purchase_order_number():
    query = _new_query()
    if not query.exec(
        """
        SELECT MAX(CAST(SUBSTR(po_number, 4) AS INTEGER))
        FROM purchase_order
        WHERE po_number LIKE 'PO-%'
        """
    ):
        return "PO-1001"

    next_no = 1001
    if query.next() and query.value(0) is not None:
        try:
            next_no = max(int(query.value(0)) + 1, 1001)
        except (TypeError, ValueError):
            next_no = 1001

    return f"PO-{next_no}"


def insert_purchase_order_header(payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO purchase_order (
            po_number,
            supplier,
            po_date,
            expected_delivery_date,
            status,
            total_value,
            notes,
            session_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(payload["po_number"])
    query.addBindValue(payload["supplier"])
    query.addBindValue(payload["po_date"])
    query.addBindValue(payload["expected_delivery_date"])
    query.addBindValue(payload["status"])
    query.addBindValue(payload["total_value"])
    query.addBindValue(payload["notes"])
    query.addBindValue(payload["session_id"])

    if not query.exec():
        raise Exception(f"Failed to save purchase order: {query.lastError().text()}")

    po_id = query.lastInsertId()
    if po_id is None:
        raise Exception("Purchase order saved, but no ID was returned.")
    try:
        return int(po_id)
    except (TypeError, ValueError):
        raise Exception("Purchase order saved, but returned ID was invalid.")


def insert_purchase_order_line(po_id, row_payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO purchase_order_line (po_id, product, qty_ordered, unit_price, total_price)
        VALUES (?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(po_id)
    query.addBindValue(row_payload["product"])
    query.addBindValue(row_payload["qty_ordered"])
    query.addBindValue(row_payload["unit_price"])
    query.addBindValue(row_payload["total_price"])

    if not query.exec():
        raise Exception(f"Failed to save purchase order line: {query.lastError().text()}")

    return query.lastInsertId()
