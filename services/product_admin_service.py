def _new_query():
    from PySide6.QtSql import QSqlQuery

    return QSqlQuery()

from medic.services.db_transaction_service import run_in_transaction


def fetch_manufacturer_lookup():
    lookup = {}
    query = _new_query()
    if not query.exec("SELECT id, name FROM manufacturer"):
        raise Exception(f"Failed to load manufacturers: {query.lastError().text()}")

    while query.next():
        try:
            key = str(int(query.value(0)))
        except Exception:
            continue
        lookup[key] = str(query.value(1) or "")

    return lookup


def resolve_auth_user_id(username):
    normalized_username = str(username or "").strip()
    if not normalized_username:
        return None

    query = _new_query()
    query.prepare("SELECT id FROM auth WHERE username = ? LIMIT 1")
    query.addBindValue(normalized_username)
    if query.exec() and query.next():
        return int(query.value(0) or 0)
    return None


def search_price_change_products(search_text, *, limit=10):
    normalized_search = str(search_text or "").strip()
    if not normalized_search:
        return []

    query = _new_query()
    query.prepare(
        f"""
        SELECT
            p.id,
            COALESCE(p.display_name, '') AS display_name,
            COALESCE(CAST(p.code AS TEXT), '') AS code,
            COALESCE((
                SELECT pp.pack_price
                FROM price_pack pp
                WHERE pp.product_id = p.id
                ORDER BY pp.is_default DESC, pp.id ASC
                LIMIT 1
            ), 0) AS current_price
        FROM product p
        WHERE
            p.display_name LIKE ?
            OR TRIM(CAST(p.code AS TEXT)) LIKE ?
        ORDER BY p.display_name ASC
        LIMIT {int(limit)}
        """
    )
    query.addBindValue(f"%{normalized_search}%")
    query.addBindValue(f"%{normalized_search}%")

    if not query.exec():
        raise Exception(f"Failed to search products: {query.lastError().text()}")

    results = []
    while query.next():
        results.append(
            {
                "product_id": int(query.value(0) or 0),
                "product_name": str(query.value(1) or ""),
                "code": str(query.value(2) or ""),
                "current_price": float(query.value(3) or 0.0),
            }
        )
    return results


def resolve_price_change_product(entered_text):
    normalized_text = str(entered_text or "").strip()
    if not normalized_text:
        return None

    query = _new_query()
    query.prepare(
        """
        SELECT
            p.id,
            COALESCE(p.display_name, '') AS display_name,
            COALESCE(CAST(p.code AS TEXT), '') AS code,
            COALESCE((
                SELECT pp.pack_price
                FROM price_pack pp
                WHERE pp.product_id = p.id
                ORDER BY pp.is_default DESC, pp.id ASC
                LIMIT 1
            ), 0) AS current_price
        FROM product p
        WHERE
            UPPER(TRIM(p.display_name)) = UPPER(TRIM(?))
            OR TRIM(CAST(p.code AS TEXT)) = ?
        ORDER BY p.display_name ASC
        LIMIT 1
        """
    )
    query.addBindValue(normalized_text)
    query.addBindValue(normalized_text)

    if not query.exec():
        raise Exception(f"Failed to search product: {query.lastError().text()}")

    if not query.next():
        return None

    return {
        "product_id": int(query.value(0) or 0),
        "product_name": str(query.value(1) or ""),
        "code": str(query.value(2) or ""),
        "current_price": float(query.value(3) or 0.0),
    }


def update_product_default_pack_price(product_id, new_price):
    query = _new_query()
    query.prepare(
        """
        UPDATE price_pack
        SET pack_price = ?
        WHERE id = (
            SELECT id
            FROM price_pack
            WHERE product_id = ?
            ORDER BY is_default DESC, id ASC
            LIMIT 1
        )
        """
    )
    query.addBindValue(new_price)
    query.addBindValue(product_id)

    if not query.exec():
        raise Exception(query.lastError().text())
    if query.numRowsAffected() == 0:
        raise Exception("No default price row found.")
    return True


def insert_price_change_log(product_id, previous_price, new_price, *, source, user_id, username):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO price_changes (
            product_id,
            previous_price,
            new_price,
            source,
            user_id,
            username
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(product_id)
    query.addBindValue(previous_price)
    query.addBindValue(new_price)
    query.addBindValue(source)
    query.addBindValue(user_id)
    query.addBindValue(username)

    if not query.exec():
        raise Exception(query.lastError().text())
    return query.lastInsertId()


def apply_price_changes(changed_rows, *, source, user_id, username):
    changed_rows = list(changed_rows or [])
    if not changed_rows:
        return 0

    changed_count = 0
    for row in changed_rows:
        product_id = int(row["product_id"])
        previous_price = float(row["previous_price"])
        new_price = float(row["new_price"])

        update_product_default_pack_price(product_id, new_price)
        insert_price_change_log(
            product_id,
            previous_price,
            new_price,
            source=source,
            user_id=user_id,
            username=username,
        )
        changed_count += 1

    return changed_count


def save_price_changes(changed_rows, *, source, user_id, username):
    normalized_rows = list(changed_rows or [])
    if not normalized_rows:
        return 0

    return run_in_transaction(
        lambda: apply_price_changes(
            normalized_rows,
            source=source,
            user_id=user_id,
            username=username,
        ),
        start_error_message="Could not start price change transaction.",
        commit_error_message="Could not commit price changes.",
    )
