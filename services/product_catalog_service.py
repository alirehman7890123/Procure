def _new_query():
    from PySide6.QtSql import QSqlQuery

    return QSqlQuery()


VALID_STOCK_FILTERS = {"All", "Available", "In Stock", "Out of Stock"}
VALID_SEARCH_CATEGORIES = {"Product", "Brand", "All"}


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
            COALESCE(bs.total_stock, 0) AS total_stock
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
            COALESCE(bs.total_stock, 0) AS total_stock
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
            COALESCE(bs.total_stock, 0) AS total_stock
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
