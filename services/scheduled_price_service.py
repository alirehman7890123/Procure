from datetime import date, datetime

from PySide6.QtSql import QSqlDatabase, QSqlQuery

try:
    from medic.utilities.activity_logger import log_activity
except ModuleNotFoundError:
    from utilities.activity_logger import log_activity
try:
    from medic.services.product_admin_service import (
        insert_price_change_log,
        resolve_auth_user_id,
        update_product_default_pack_price,
    )
except ModuleNotFoundError:
    from services.product_admin_service import (
        insert_price_change_log,
        resolve_auth_user_id,
        update_product_default_pack_price,
    )


def _new_query():
    return QSqlQuery()


def _today_iso():
    return date.today().isoformat()


def ensure_scheduled_price_schema():
    query = _new_query()
    if not query.exec(
        """
        CREATE TABLE IF NOT EXISTS scheduled_price_change (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            purchase_id INTEGER,
            previous_price REAL NOT NULL DEFAULT 0,
            new_price REAL NOT NULL DEFAULT 0,
            effective_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'scheduled',
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            created_by INTEGER,
            created_by_username TEXT,
            applied_at TEXT,
            applied_by TEXT,
            cancelled_at TEXT,
            cancelled_by TEXT,
            notes TEXT,
            FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE RESTRICT,
            FOREIGN KEY (purchase_id) REFERENCES purchase(id) ON DELETE SET NULL
        )
        """
    ):
        raise Exception(f"Failed to create scheduled_price_change table: {query.lastError().text()}")

    if not query.exec(
        """
        CREATE INDEX IF NOT EXISTS idx_scheduled_price_change_due
        ON scheduled_price_change(status, effective_date)
        """
    ):
        raise Exception(f"Failed to create scheduled price index: {query.lastError().text()}")

    return True


def save_scheduled_price_change(
    *,
    product_id,
    purchase_id,
    previous_price,
    new_price,
    effective_date,
    created_by=None,
    created_by_username="",
    notes=None,
):
    ensure_scheduled_price_schema()
    product_id = int(product_id)
    purchase_id = int(purchase_id) if purchase_id not in (None, "") else None
    previous_price = float(previous_price or 0.0)
    new_price = float(new_price or 0.0)
    effective_date = str(effective_date or "").strip()
    created_by_username = str(created_by_username or "").strip()

    if not effective_date:
        raise Exception("Effective date is required.")

    existing_query = _new_query()
    existing_query.prepare(
        """
        SELECT id
        FROM scheduled_price_change
        WHERE product_id = ? AND status = 'scheduled'
        ORDER BY id DESC
        LIMIT 1
        """
    )
    existing_query.addBindValue(product_id)
    if not existing_query.exec():
        raise Exception(f"Failed to check existing scheduled price change: {existing_query.lastError().text()}")

    if existing_query.next():
        change_id = int(existing_query.value(0) or 0)
        update_query = _new_query()
        update_query.prepare(
            """
            UPDATE scheduled_price_change
            SET
                purchase_id = ?,
                previous_price = ?,
                new_price = ?,
                effective_date = ?,
                created_by = ?,
                created_by_username = ?,
                notes = ?,
                created_at = datetime('now','localtime'),
                applied_at = NULL,
                applied_by = NULL,
                cancelled_at = NULL,
                cancelled_by = NULL,
                status = 'scheduled'
            WHERE id = ?
            """
        )
        update_query.addBindValue(purchase_id)
        update_query.addBindValue(previous_price)
        update_query.addBindValue(new_price)
        update_query.addBindValue(effective_date)
        update_query.addBindValue(created_by)
        update_query.addBindValue(created_by_username or None)
        update_query.addBindValue(notes or None)
        update_query.addBindValue(change_id)
        if not update_query.exec():
            raise Exception(f"Failed to update scheduled price change: {update_query.lastError().text()}")
        return change_id

    insert_query = _new_query()
    insert_query.prepare(
        """
        INSERT INTO scheduled_price_change (
            product_id,
            purchase_id,
            previous_price,
            new_price,
            effective_date,
            status,
            created_by,
            created_by_username,
            notes
        ) VALUES (?, ?, ?, ?, ?, 'scheduled', ?, ?, ?)
        """
    )
    insert_query.addBindValue(product_id)
    insert_query.addBindValue(purchase_id)
    insert_query.addBindValue(previous_price)
    insert_query.addBindValue(new_price)
    insert_query.addBindValue(effective_date)
    insert_query.addBindValue(created_by)
    insert_query.addBindValue(created_by_username or None)
    insert_query.addBindValue(notes or None)
    if not insert_query.exec():
        raise Exception(f"Failed to insert scheduled price change: {insert_query.lastError().text()}")
    return int(insert_query.lastInsertId() or 0)


def apply_due_scheduled_price_changes(*, today=None, applied_by="system"):
    ensure_scheduled_price_schema()
    today = str(today or _today_iso()).strip()
    applied_by = str(applied_by or "system").strip() or "system"
    applied_user_id = resolve_auth_user_id(applied_by)

    query = _new_query()
    query.prepare(
        """
        SELECT
            spc.id,
            spc.product_id,
            spc.previous_price,
            spc.new_price,
            spc.effective_date,
            COALESCE(p.display_name, '')
        FROM scheduled_price_change spc
        LEFT JOIN product p ON p.id = spc.product_id
        WHERE spc.status = 'scheduled'
          AND spc.effective_date <= ?
        ORDER BY spc.effective_date ASC, spc.id ASC
        """
    )
    query.addBindValue(today)
    if not query.exec():
        raise Exception(f"Failed to load due scheduled price changes: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "id": int(query.value(0) or 0),
                "product_id": int(query.value(1) or 0),
                "previous_price": float(query.value(2) or 0.0),
                "new_price": float(query.value(3) or 0.0),
                "effective_date": str(query.value(4) or ""),
                "product_name": str(query.value(5) or "").strip(),
            }
        )

    if not rows:
        return {"count": 0, "products": []}

    db = QSqlDatabase.database()
    started_tx = False
    if db.isValid() and not db.driver().hasFeature(db.driver().Transactions):
        started_tx = False
    else:
        started_tx = db.transaction()

    try:
        applied_products = []
        for row in rows:
            update_product_default_pack_price(row["product_id"], row["new_price"])
            insert_price_change_log(
                row["product_id"],
                row["previous_price"],
                row["new_price"],
                source="scheduled_price_change",
                user_id=applied_user_id,
                username=applied_by,
            )

            status_query = _new_query()
            status_query.prepare(
                """
                UPDATE scheduled_price_change
                SET
                    status = 'applied',
                    applied_at = datetime('now','localtime'),
                    applied_by = ?
                WHERE id = ?
                """
            )
            status_query.addBindValue(applied_by)
            status_query.addBindValue(row["id"])
            if not status_query.exec():
                raise Exception(f"Failed to mark scheduled price change as applied: {status_query.lastError().text()}")

            log_activity(
                category="price",
                action="price_change_applied",
                entity_type="product",
                entity_id=row["product_id"],
                note=(
                    f"Scheduled selling price applied for {row['product_name'] or f'Product {row['product_id']}'}. "
                    f"Pack price changed from {row['previous_price']} to {row['new_price']}. "
                    f"Effective date: {row['effective_date']}."
                ),
                previous_value=str(row["previous_price"]),
                new_value=str(row["new_price"]),
            )
            applied_products.append(row["product_name"] or f"Product {row['product_id']}")

        if started_tx and not db.commit():
            raise Exception("Could not commit scheduled price changes.")
        return {"count": len(applied_products), "products": applied_products}
    except Exception:
        if started_tx:
            db.rollback()
        raise
