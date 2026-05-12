import csv
import re
import sys
from pathlib import Path


def _new_query():
    from PySide6.QtSql import QSqlQuery

    return QSqlQuery()


VALID_STOCK_FILTERS = {"All", "Available", "In Stock", "Out of Stock"}
VALID_SEARCH_CATEGORIES = {"Product", "Brand", "All"}


def _format_product_label(display_name, pack_size):
    name = str(display_name or "").strip()
    try:
        pack_size_num = int(float(pack_size))
    except (TypeError, ValueError):
        pack_size_num = 0

    if pack_size_num > 0:
        return f"{name} [{pack_size_num}s]"
    return name


def build_product_stock_filter_clause(stock_filter):
    normalized = str(stock_filter or "All").strip()
    if normalized not in VALID_STOCK_FILTERS:
        normalized = "All"

    if normalized == "Available":
        return " AND p.status = 'used'"
    if normalized == "In Stock":
        return " AND p.status = 'used' AND COALESCE(bs.total_stock, 0) > 0"
    if normalized == "Out of Stock":
        return " AND p.status = 'used' AND COALESCE(bs.total_stock, 0) <= 0"
    return ""


def _product_listing_from_clause():
    return """
        FROM product p
        LEFT JOIN manufacturer m ON p.manufacturer_id = m.id
        LEFT JOIN (
            SELECT product_id, SUM(quantity_remaining) AS total_stock
            FROM batch
            GROUP BY product_id
        ) bs ON p.id = bs.product_id
    """


def _read_product_listing_rows(query):
    rows = []
    while query.next():
        rows.append(
            {
                "product_id": int(query.value(0) or 0),
                "display_name": str(query.value(1) or ""),
                "manufacturer_name": str(query.value(2) or ""),
                "total_stock": query.value(3) or 0,
                "prescription_required": bool(int(query.value(4) or 0)),
            }
        )
    return rows


def fetch_used_product_count():
    query = _new_query()
    if not query.exec("SELECT COUNT(*) FROM product WHERE status = 'used'"):
        raise Exception(f"Failed to load product count: {query.lastError().text()}")
    if query.next():
        return int(query.value(0) or 0)
    return 0


def fetch_low_stock_rows():
    query = _new_query()
    query.prepare(
        """
        SELECT 
            p.id,
            p.display_name,
            p.code,
            p.generic_name,
            p.brand
        FROM product p
        LEFT JOIN batch b ON b.product_id = p.id
        LEFT JOIN (
            SELECT product_id, MAX(COALESCE(reorder_level, 0)) AS reorder_level
            FROM price_pack
            GROUP BY product_id
        ) pp ON pp.product_id = p.id
        WHERE p.status = 'used'
        GROUP BY p.id, p.display_name, p.code, p.generic_name, p.brand
        HAVING COALESCE(SUM(b.quantity_remaining), 0) <= MAX(COALESCE(pp.reorder_level, 0))
        ORDER BY p.display_name ASC
        """
    )

    if not query.exec():
        raise Exception(f"Failed to load low stock products: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "id": int(query.value(0) or 0),
                "name": str(query.value(1) or ""),
                "code": str(query.value(2) or ""),
                "generic": str(query.value(3) or ""),
                "brand": str(query.value(4) or ""),
            }
        )
    return rows


def fetch_expired_product_rows():
    query = _new_query()
    query.prepare(
        """
        SELECT DISTINCT
            p.id,
            p.display_name,
            p.code,
            p.generic_name,
            p.brand
        FROM product p
        JOIN batch b ON b.product_id = p.id
        WHERE
            p.status = 'used'
            AND b.quantity_remaining > 0
            AND b.expiry_date IS NOT NULL
            AND (
                CASE
                    WHEN b.expiry_date LIKE '____-__-__' THEN date(b.expiry_date)
                    WHEN b.expiry_date LIKE '__-__-____'
                        THEN date(substr(b.expiry_date, 7, 4) || '-' || substr(b.expiry_date, 4, 2) || '-' || substr(b.expiry_date, 1, 2))
                    ELSE NULL
                END
            ) < date('now', 'localtime')
        ORDER BY p.display_name ASC
        """
    )

    if not query.exec():
        raise Exception(f"Failed to load expired products: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "id": int(query.value(0) or 0),
                "name": str(query.value(1) or ""),
                "code": str(query.value(2) or ""),
                "generic": str(query.value(3) or ""),
                "brand": str(query.value(4) or ""),
            }
        )
    return rows


def _resolve_catalog_path(relative_path):
    relative = Path(relative_path)
    candidates = []

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / relative)

    module_root = Path(__file__).resolve().parent.parent
    candidates.append(module_root / relative)
    candidates.append(Path.cwd() / relative)

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return str(candidates[0])


def fetch_master_catalog_rows(*, relative_path="master_products.csv", manufacturer_lookup=None):
    if manufacturer_lookup is None:
        from medic.services.product_admin_service import fetch_manufacturer_lookup

        manufacturer_lookup = fetch_manufacturer_lookup()

    csv_path = _resolve_catalog_path(relative_path)
    rows = []
    with open(csv_path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader, None)

        for row in reader:
            if not row or len(row) < 8:
                continue

            manufacturer_id = row[7].strip()
            rows.append(
                {
                    "reg_no": row[0].strip(),
                    "name": row[1].strip(),
                    "generic": row[2].strip(),
                    "form": row[3].strip(),
                    "strength": row[4].strip(),
                    "packing": row[5].strip(),
                    "size": row[6].strip(),
                    "manufacturer_id": manufacturer_id,
                    "manufacturer_name": manufacturer_lookup.get(manufacturer_id, ""),
                }
            )

    return {
        "csv_path": csv_path,
        "rows": rows,
        "manufacturer_count": len(manufacturer_lookup),
    }


def fetch_product_by_barcode(code_text, *, stock_filter="All"):
    normalized_code = str(code_text or "").strip()
    if not normalized_code:
        return None

    from_clause = _product_listing_from_clause()
    where_clause = "WHERE TRIM(CAST(p.code AS TEXT)) = ?"
    where_clause += build_product_stock_filter_clause(stock_filter)

    query = _new_query()
    query.prepare(
        f"""
        SELECT
            p.id,
            p.display_name,
            COALESCE(m.name, '') AS manufacturer_name,
            COALESCE(bs.total_stock, 0) AS total_stock,
            COALESCE(p.prescription_required, 0) AS prescription_required
        {from_clause}
        {where_clause}
        LIMIT 1
        """
    )
    query.addBindValue(normalized_code)

    if not query.exec():
        raise Exception(f"Failed to search barcode: {query.lastError().text()}")

    rows = _read_product_listing_rows(query)
    return rows[0] if rows else None


def search_products(*, text, category="Product", stock_filter="All", page=1, page_size=50):
    normalized_text = str(text or "").strip()
    normalized_category = str(category or "Product").strip()
    if normalized_category not in VALID_SEARCH_CATEGORIES:
        normalized_category = "Product"

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 50

    from_clause = _product_listing_from_clause()
    where_clause = "WHERE 1=1"
    where_clause += build_product_stock_filter_clause(stock_filter)

    pattern = f"%{normalized_text}%"
    prefix_pattern = f"{normalized_text}%"
    bindings = []
    order_bindings = []
    order_clause = "ORDER BY p.id DESC"

    if normalized_category == "Product":
        where_clause += " AND p.display_name LIKE ?"
        bindings.append(pattern)
        order_clause = """
            ORDER BY
                CASE
                    WHEN UPPER(p.display_name) = UPPER(?) THEN 0
                    WHEN UPPER(p.display_name) LIKE UPPER(?) THEN 1
                    ELSE 2
                END,
                p.display_name ASC,
                p.id DESC
        """
        order_bindings.extend([normalized_text, prefix_pattern])
    elif normalized_category == "Brand":
        where_clause += " AND COALESCE(m.name, '') LIKE ?"
        bindings.append(pattern)
        order_clause = """
            ORDER BY
                CASE
                    WHEN UPPER(COALESCE(m.name, '')) = UPPER(?) THEN 0
                    WHEN UPPER(COALESCE(m.name, '')) LIKE UPPER(?) THEN 1
                    ELSE 2
                END,
                COALESCE(m.name, '') ASC,
                p.display_name ASC,
                p.id DESC
        """
        order_bindings.extend([normalized_text, prefix_pattern])
    else:
        where_clause += """
            AND (
                p.display_name LIKE ?
                OR COALESCE(m.name, '') LIKE ?
            )
        """
        bindings.extend([pattern, pattern])
        order_clause = """
            ORDER BY
                CASE
                    WHEN UPPER(p.display_name) = UPPER(?) THEN 0
                    WHEN UPPER(p.display_name) LIKE UPPER(?) THEN 1
                    WHEN UPPER(COALESCE(m.name, '')) = UPPER(?) THEN 2
                    WHEN UPPER(COALESCE(m.name, '')) LIKE UPPER(?) THEN 3
                    ELSE 4
                END,
                p.display_name ASC,
                p.id DESC
        """
        order_bindings.extend([normalized_text, prefix_pattern, normalized_text, prefix_pattern])

    count_query = _new_query()
    count_query.prepare(
        f"""
        SELECT COUNT(*)
        {from_clause}
        {where_clause}
        """
    )
    for value in bindings:
        count_query.addBindValue(value)

    if not count_query.exec():
        raise Exception(f"Failed to count products: {count_query.lastError().text()}")

    total_records = 0
    if count_query.next():
        total_records = int(count_query.value(0) or 0)

    offset = (page - 1) * page_size
    data_query = _new_query()
    data_query.prepare(
        f"""
        SELECT
            p.id,
            p.display_name,
            COALESCE(m.name, '') AS manufacturer_name,
            COALESCE(bs.total_stock, 0) AS total_stock,
            COALESCE(p.prescription_required, 0) AS prescription_required
        {from_clause}
        {where_clause}
        {order_clause}
        LIMIT ? OFFSET ?
        """
    )
    for value in bindings:
        data_query.addBindValue(value)
    for value in order_bindings:
        data_query.addBindValue(value)
    data_query.addBindValue(page_size)
    data_query.addBindValue(offset)

    if not data_query.exec():
        raise Exception(f"Failed to search products: {data_query.lastError().text()}")

    rows = _read_product_listing_rows(data_query)
    return {
        "rows": rows,
        "total_records": total_records,
        "page": page,
        "page_size": page_size,
    }


def fetch_product_listing_page(*, stock_filter="All", page=1, page_size=50):
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 50

    from_clause = _product_listing_from_clause()
    where_clause = "WHERE 1=1"
    where_clause += build_product_stock_filter_clause(stock_filter)

    count_query = _new_query()
    count_query.prepare(
        f"""
        SELECT COUNT(*)
        {from_clause}
        {where_clause}
        """
    )
    if not count_query.exec():
        raise Exception(f"Failed to count product listing: {count_query.lastError().text()}")

    total_records = 0
    if count_query.next():
        total_records = int(count_query.value(0) or 0)

    offset = (page - 1) * page_size
    data_query = _new_query()
    data_query.prepare(
        f"""
        SELECT 
            p.id,
            p.display_name,
            COALESCE(m.name, '') AS manufacturer_name,
            COALESCE(bs.total_stock, 0) AS total_stock,
            COALESCE(p.prescription_required, 0) AS prescription_required
        {from_clause}
        {where_clause}
        ORDER BY p.id DESC
        LIMIT ? OFFSET ?
        """
    )
    data_query.addBindValue(page_size)
    data_query.addBindValue(offset)

    if not data_query.exec():
        raise Exception(f"Failed to load product listing: {data_query.lastError().text()}")

    rows = _read_product_listing_rows(data_query)
    return {
        "rows": rows,
        "total_records": total_records,
        "page": page,
        "page_size": page_size,
    }


def fetch_sales_product_by_code(code_text):
    normalized_code = str(code_text or "").strip()
    if not normalized_code:
        return None

    query = _new_query()
    query.prepare(
        """
        SELECT
            p.id,
            p.display_name,
            COALESCE(pp.unit_price, 0),
            COALESCE(dg.id, 0),
            COALESCE(dg.discount_percent, 0),
            COALESCE(dg.name, ''),
            COALESCE(dg.fixed_amount, 0),
            COALESCE(dg.apply_on_sale, 1),
            COALESCE(tg.id, 0),
            CASE WHEN COALESCE(tg.apply_on_sale, 1) = 1 THEN COALESCE(tg.tax_percent, 0) ELSE 0 END,
            COALESCE(tg.fixed_amount, 0),
            COALESCE(tg.apply_on_sale, 1),
            COALESCE(tg.name, ''),
            COALESCE(p.prescription_required, 0),
            COALESCE((
                SELECT SUM(quantity_remaining)
                FROM batch
                WHERE product_id = p.id
                  AND quantity_remaining > 0
                  AND (
                      expiry_date IS NULL
                      OR (
                          CASE
                              WHEN expiry_date LIKE '____-__-__' THEN date(expiry_date)
                              WHEN expiry_date LIKE '__-__-____'
                                  THEN date(substr(expiry_date, 7, 4) || '-' || substr(expiry_date, 4, 2) || '-' || substr(expiry_date, 1, 2))
                              ELSE NULL
                          END
                      ) >= date('now', 'localtime')
                  )
            ), 0) AS available_stock
        FROM product p
        LEFT JOIN discount_group dg ON dg.id = p.discount_group_id
        LEFT JOIN tax_group tg ON tg.id = p.tax_group_id
        LEFT JOIN price_pack pp ON pp.id = (
            SELECT id
            FROM price_pack
            WHERE product_id = p.id
            ORDER BY is_default DESC, id ASC
            LIMIT 1
        )
        WHERE TRIM(CAST(p.code AS TEXT)) = ?
          AND COALESCE(p.status, 'active') = 'used'
        LIMIT 1
        """
    )
    query.addBindValue(normalized_code)

    if not query.exec():
        raise Exception(f"Barcode product query failed: {query.lastError().text()}")
    if not query.next():
        return None

    return {
        "product_id": int(query.value(0) or 0),
        "display_name": str(query.value(1) or "").strip(),
        "unit_price": float(query.value(2) or 0.0),
        "discount_group_id": int(query.value(3) or 0) or None,
        "discount_percent": float(query.value(4) or 0.0),
        "discount_group_name": str(query.value(5) or "").strip(),
        "discount_fixed_amount": float(query.value(6) or 0.0),
        "discount_apply_on_sale": bool(int(query.value(7) or 0)),
        "tax_group_id": int(query.value(8) or 0) or None,
        "tax_percent": float(query.value(9) or 0.0),
        "tax_fixed_amount": float(query.value(10) or 0.0),
        "tax_apply_on_sale": bool(int(query.value(11) or 0)),
        "tax_group_name": str(query.value(12) or "").strip(),
        "prescription_required": bool(int(query.value(13) or 0)),
        "available_stock": int(query.value(14) or 0),
        "code": normalized_code,
    }


def search_sales_products(search_text):
    normalized_text = str(search_text or "").strip()
    query = _new_query()
    query.prepare(
        """
        SELECT p.id, p.display_name, COALESCE(p.generic_name, ''), COALESCE(pp.pack_size, 0), pp.unit_price
             , COALESCE((
                SELECT b.unit_cost
                FROM batch b
                WHERE b.product_id = p.id
                  AND b.unit_cost IS NOT NULL
                  AND b.unit_cost > 0
                ORDER BY b.id DESC
                LIMIT 1
             ), COALESCE((
                SELECT pi.rate
                FROM purchaseitem pi
                JOIN purchase pu ON pu.id = pi.purchase
                WHERE pi.product = p.id
                ORDER BY pu.id DESC, pi.id DESC
                LIMIT 1
             ), 0))
             , COALESCE(dg.id, 0)
             , COALESCE(dg.discount_percent, 0)
             , COALESCE(dg.name, '')
             , COALESCE(dg.fixed_amount, 0)
             , COALESCE(dg.apply_on_sale, 1)
             , COALESCE(tg.id, 0)
             , CASE WHEN COALESCE(tg.apply_on_sale, 1) = 1 THEN COALESCE(tg.tax_percent, 0) ELSE 0 END
             , COALESCE(tg.fixed_amount, 0)
             , COALESCE(tg.apply_on_sale, 1)
             , COALESCE(tg.name, '')
             , COALESCE(pp.margin_percent, 0)
             , COALESCE(p.status, 'active')
             , COALESCE(p.prescription_required, 0)
        FROM product p
        LEFT JOIN discount_group dg ON dg.id = p.discount_group_id
        LEFT JOIN tax_group tg ON tg.id = p.tax_group_id
        LEFT JOIN price_pack pp ON pp.id = (
            SELECT id
            FROM price_pack
            WHERE product_id = p.id
            ORDER BY is_default DESC, id DESC
            LIMIT 1
        )
        WHERE p.display_name LIKE ?
        ORDER BY p.display_name ASC
        LIMIT 50
        """
    )
    query.addBindValue(f"{normalized_text}%")

    results = []
    if not query.exec():
        raise Exception(f"Sales product search failed: {query.lastError().text()}")

    while query.next():
        product_id = int(query.value(0) or 0)
        display_name = str(query.value(1) or "").strip()
        pack_size = query.value(3)
        results.append(
            (
                _format_product_label(display_name, pack_size),
                {
                    "product_id": product_id,
                    "display_name": display_name,
                    "visible_name": _format_product_label(display_name, pack_size),
                    "generic_name": str(query.value(2) or "").strip(),
                    "unit_price": float(query.value(4) or 0.0),
                    "cost_price": float(query.value(5) or 0.0),
                    "discount_group_id": int(query.value(6) or 0) or None,
                    "discount_percent": float(query.value(7) or 0.0),
                    "discount_group_name": str(query.value(8) or "").strip(),
                    "discount_fixed_amount": float(query.value(9) or 0.0),
                    "discount_apply_on_sale": bool(int(query.value(10) or 0)),
                    "tax_group_id": int(query.value(11) or 0) or None,
                    "tax_percent": float(query.value(12) or 0.0),
                    "tax_fixed_amount": float(query.value(13) or 0.0),
                    "tax_apply_on_sale": bool(int(query.value(14) or 0)),
                    "tax_group_name": str(query.value(15) or "").strip(),
                    "target_margin_percent": float(query.value(16) or 0.0),
                    "status": str(query.value(17) or "active").strip(),
                    "prescription_required": bool(int(query.value(18) or 0)),
                },
            )
        )
    return results


def fetch_sales_product_detail(product_id):
    query = _new_query()
    query.prepare(
        """
        SELECT p.id, p.display_name, COALESCE(p.generic_name, ''), COALESCE(pp.pack_size, 0), pp.unit_price
             , COALESCE((
                SELECT b.unit_cost
                FROM batch b
                WHERE b.product_id = p.id
                  AND b.unit_cost IS NOT NULL
                  AND b.unit_cost > 0
                ORDER BY b.id DESC
                LIMIT 1
             ), COALESCE((
                SELECT pi.rate
                FROM purchaseitem pi
                JOIN purchase pu ON pu.id = pi.purchase
                WHERE pi.product = p.id
                ORDER BY pu.id DESC, pi.id DESC
                LIMIT 1
             ), 0))
             , COALESCE(dg.id, 0)
             , COALESCE(dg.discount_percent, 0)
             , COALESCE(dg.name, '')
             , COALESCE(dg.fixed_amount, 0)
             , COALESCE(dg.apply_on_sale, 1)
             , COALESCE(tg.id, 0)
             , CASE WHEN COALESCE(tg.apply_on_sale, 1) = 1 THEN COALESCE(tg.tax_percent, 0) ELSE 0 END
             , COALESCE(tg.fixed_amount, 0)
             , COALESCE(tg.apply_on_sale, 1)
             , COALESCE(tg.name, '')
             , COALESCE(pp.margin_percent, 0)
             , COALESCE(p.status, 'active')
             , COALESCE(p.prescription_required, 0)
        FROM product p
        LEFT JOIN discount_group dg ON dg.id = p.discount_group_id
        LEFT JOIN tax_group tg ON tg.id = p.tax_group_id
        LEFT JOIN price_pack pp ON pp.id = (
            SELECT id
            FROM price_pack
            WHERE product_id = p.id
            ORDER BY is_default DESC, id DESC
            LIMIT 1
        )
        WHERE p.id = ?
        LIMIT 1
        """
    )
    query.addBindValue(int(product_id))
    if not query.exec():
        raise Exception(f"Sales product lookup failed: {query.lastError().text()}")
    if not query.next():
        return None

    display_name = str(query.value(1) or "").strip()
    pack_size = query.value(3)
    return {
        "product_id": int(query.value(0) or 0),
        "display_name": display_name,
        "visible_name": _format_product_label(display_name, pack_size),
        "generic_name": str(query.value(2) or "").strip(),
        "unit_price": float(query.value(4) or 0.0),
        "cost_price": float(query.value(5) or 0.0),
        "discount_group_id": int(query.value(6) or 0) or None,
        "discount_percent": float(query.value(7) or 0.0),
        "discount_group_name": str(query.value(8) or "").strip(),
        "discount_fixed_amount": float(query.value(9) or 0.0),
        "discount_apply_on_sale": bool(int(query.value(10) or 0)),
        "tax_group_id": int(query.value(11) or 0) or None,
        "tax_percent": float(query.value(12) or 0.0),
        "tax_fixed_amount": float(query.value(13) or 0.0),
        "tax_apply_on_sale": bool(int(query.value(14) or 0)),
        "tax_group_name": str(query.value(15) or "").strip(),
        "target_margin_percent": float(query.value(16) or 0.0),
        "status": str(query.value(17) or "active").strip(),
        "prescription_required": bool(int(query.value(18) or 0)),
    }


def find_product_id_by_display_name(display_name):
    normalized_name = re.sub(r"\s*\[\d+s\]\s*$", "", str(display_name or "").strip(), flags=re.IGNORECASE)
    query = _new_query()
    query.prepare(
        """
        SELECT id
        FROM product
        WHERE LOWER(TRIM(display_name)) = LOWER(TRIM(?))
        LIMIT 1
        """
    )
    query.addBindValue(normalized_name)
    if not query.exec():
        raise Exception(f"Product name lookup failed: {query.lastError().text()}")
    if query.next():
        return int(query.value(0) or 0)
    return None


def fetch_hold_row_product_data(product_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            p.display_name,
            COALESCE(pp.unit_price, 0),
            COALESCE(dg.id, 0),
            COALESCE(dg.discount_percent, 0),
            COALESCE(dg.name, ''),
            COALESCE(dg.fixed_amount, 0),
            COALESCE(dg.apply_on_sale, 1),
            COALESCE(tg.id, 0),
            CASE WHEN COALESCE(tg.apply_on_sale, 1) = 1 THEN COALESCE(tg.tax_percent, 0) ELSE 0 END,
            COALESCE(tg.fixed_amount, 0),
            COALESCE(tg.apply_on_sale, 1),
            COALESCE(tg.name, ''),
            COALESCE(pp.margin_percent, 0)
        FROM product p
        LEFT JOIN discount_group dg ON dg.id = p.discount_group_id
        LEFT JOIN tax_group tg ON tg.id = p.tax_group_id
        LEFT JOIN price_pack pp ON pp.id = (
            SELECT id
            FROM price_pack
            WHERE product_id = p.id
            ORDER BY is_default DESC, id ASC
            LIMIT 1
        )
        WHERE p.id = ?
        LIMIT 1
        """
    )
    query.addBindValue(int(product_id))

    if not query.exec():
        raise Exception(f"Hold row product lookup failed: {query.lastError().text()}")
    if not query.next():
        return None

    return {
        "product_id": int(product_id),
        "display_name": str(query.value(0) or "").strip(),
        "unit_price": float(query.value(1) or 0.0),
        "cost_price": 0.0,
        "discount_group_id": int(query.value(2) or 0) or None,
        "discount_percent": float(query.value(3) or 0.0),
        "discount_group_name": str(query.value(4) or "").strip(),
        "discount_fixed_amount": float(query.value(5) or 0.0),
        "discount_apply_on_sale": bool(int(query.value(6) or 0)),
        "tax_group_id": int(query.value(7) or 0) or None,
        "tax_percent": float(query.value(8) or 0.0),
        "tax_fixed_amount": float(query.value(9) or 0.0),
        "tax_apply_on_sale": bool(int(query.value(10) or 0)),
        "tax_group_name": str(query.value(11) or "").strip(),
        "target_margin_percent": float(query.value(12) or 0.0),
    }


def fetch_available_product_quantity(product_id):
    query = _new_query()
    query.prepare(
        """
        SELECT COALESCE(SUM(quantity_remaining), 0)
        FROM batch
        WHERE product_id = ?
        AND quantity_remaining > 0
        AND (
            expiry_date IS NULL
            OR (
                CASE
                    WHEN expiry_date LIKE '____-__-__' THEN date(expiry_date)
                    WHEN expiry_date LIKE '__-__-____'
                        THEN date(substr(expiry_date, 7, 4) || '-' || substr(expiry_date, 4, 2) || '-' || substr(expiry_date, 1, 2))
                    ELSE NULL
                END
            ) >= date('now', 'localtime')
        )
        """
    )
    query.addBindValue(int(product_id))

    if not query.exec():
        raise Exception(f"Available stock lookup failed: {query.lastError().text()}")
    if query.next():
        return int(query.value(0) or 0)
    return 0
