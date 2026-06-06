_SCHEMA_READY = False


def _new_query(db=None):
    from PySide6.QtSql import QSqlQuery

    if db is not None:
        return QSqlQuery(db)
    return QSqlQuery()


def ensure_product_sales_rank_schema():
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return True

    query = _new_query()
    if not query.exec(
        """
        CREATE TABLE IF NOT EXISTS product_sales_rank (
            product_id INTEGER PRIMARY KEY,
            sale_count INTEGER NOT NULL DEFAULT 0,
            qty_sold REAL NOT NULL DEFAULT 0,
            last_sold_at TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE
        )
        """
    ):
        raise Exception(f"Product sales rank table creation failed: {query.lastError().text()}")

    if not query.exec(
        """
        CREATE INDEX IF NOT EXISTS idx_product_sales_rank_order
        ON product_sales_rank(sale_count DESC, qty_sold DESC, last_sold_at DESC)
        """
    ):
        raise Exception(f"Product sales rank index creation failed: {query.lastError().text()}")

    _SCHEMA_READY = True
    return True


def record_product_sale(product_id, qty_sold, *, db=None):
    ensure_product_sales_rank_schema()

    normalized_product_id = int(product_id or 0)
    if normalized_product_id <= 0:
        raise ValueError("A valid product is required for sales ranking.")

    try:
        normalized_qty = float(qty_sold or 0.0)
    except (TypeError, ValueError):
        normalized_qty = 0.0
    if normalized_qty <= 0:
        normalized_qty = 0.0

    query = _new_query(db)
    query.prepare(
        """
        INSERT INTO product_sales_rank (
            product_id,
            sale_count,
            qty_sold,
            last_sold_at
        )
        VALUES (?, 1, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(product_id) DO UPDATE SET
            sale_count = product_sales_rank.sale_count + 1,
            qty_sold = product_sales_rank.qty_sold + excluded.qty_sold,
            last_sold_at = CURRENT_TIMESTAMP
        """
    )
    query.addBindValue(normalized_product_id)
    query.addBindValue(normalized_qty)
    if not query.exec():
        raise Exception(f"Failed to update product sales rank: {query.lastError().text()}")

    return True
