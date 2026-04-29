from PySide6.QtSql import QSqlDatabase, QSqlQuery
from datetime import datetime
import bcrypt

try:
    from medic.services.product_media_service import (
        clear_product_media_fields,
        fetch_product_media,
        save_product_media,
        update_product_media_fields,
    )
    from medic.services.product_admin_service import insert_price_change_log
except ModuleNotFoundError:
    from services.product_media_service import (
        clear_product_media_fields,
        fetch_product_media,
        save_product_media,
        update_product_media_fields,
    )
    from services.product_admin_service import insert_price_change_log


DEFAULT_MARGIN_PERCENT = 14.5


def _new_query(db=None):
    if db is not None:
        return QSqlQuery(db)
    return QSqlQuery()


def fetch_manufacturer_options(*, active_only=True):
    query = _new_query()
    sql = "SELECT id, name FROM manufacturer"
    if active_only:
        sql += " WHERE status = 'active'"
    sql += " ORDER BY name"

    if not query.exec(sql):
        raise Exception(f"Failed to load manufacturers: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "id": query.value(0),
                "name": str(query.value(1) or "").strip(),
            }
        )
    return rows


def ensure_manufacturer(name):
    normalized_name = str(name or "").strip()
    if not normalized_name:
        return None

    query = _new_query()
    query.prepare("SELECT id FROM manufacturer WHERE LOWER(TRIM(name)) = LOWER(TRIM(?)) LIMIT 1")
    query.addBindValue(normalized_name)
    if not query.exec():
        raise Exception(f"Failed to lookup manufacturer: {query.lastError().text()}")
    if query.next():
        return int(query.value(0) or 0)

    insert_query = _new_query()
    insert_query.prepare("INSERT INTO manufacturer (name) VALUES (?)")
    insert_query.addBindValue(normalized_name)
    if not insert_query.exec():
        raise Exception(f"Failed to insert manufacturer: {insert_query.lastError().text()}")
    return int(insert_query.lastInsertId())


def _fetch_group_options(table_name, percent_column):
    query = _new_query()
    query.prepare(
        f"""
        SELECT id, name, {percent_column}, COALESCE(fixed_amount, 0), COALESCE(apply_on_sale, 1)
        FROM {table_name}
        WHERE status = 'active'
        ORDER BY name
        """
    )
    if not query.exec():
        raise Exception(f"Failed to load {table_name}: {query.lastError().text()}")

    rows = []
    while query.next():
        group_id = query.value(0)
        name = str(query.value(1) or "").strip()
        percent = float(query.value(2) or 0.0)
        fixed_amount = float(query.value(3) or 0.0)
        apply_on_sale = bool(int(query.value(4) or 0))
        rows.append(
            {
                "id": group_id,
                "label": (
                    f"{name} ({percent:.2f}% + {fixed_amount:.2f}, "
                    f"{'Sale On' if apply_on_sale else 'Sale Off'})"
                ),
            }
        )
    return rows


def fetch_tax_group_options():
    return _fetch_group_options("tax_group", "tax_percent")


def fetch_discount_group_options():
    return _fetch_group_options("discount_group", "discount_percent")


def fetch_product_autofill(product_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            generic_name,
            manufacturer_id,
            strength,
            discount_group_id,
            tax_group_id,
            COALESCE(rack, ''),
            COALESCE(prescription_required, 0),
            (
                SELECT pack_size
                FROM price_pack
                WHERE product_id = product.id
                ORDER BY is_default DESC, id DESC
                LIMIT 1
            ) AS pack_size,
            (
                SELECT pack_price
                FROM price_pack
                WHERE product_id = product.id
                ORDER BY is_default DESC, id DESC
                LIMIT 1
            ) AS pack_price,
            (
                SELECT margin_percent
                FROM price_pack
                WHERE product_id = product.id
                ORDER BY is_default DESC, id DESC
                LIMIT 1
            ) AS margin_percent
        FROM product
        WHERE id = ?
        LIMIT 1
        """
    )
    query.addBindValue(int(product_id))

    if not query.exec():
        raise Exception(f"Failed to load product autofill: {query.lastError().text()}")
    if not query.next():
        return None

    return {
        "generic_name": str(query.value(0) or "").strip(),
        "manufacturer_id": query.value(1),
        "strength": str(query.value(2) or "").strip(),
        "discount_group_id": query.value(3),
        "tax_group_id": query.value(4),
        "rack": str(query.value(5) or "").strip(),
        "prescription_required": bool(int(query.value(6) or 0)),
        "pack_size": query.value(7),
        "pack_price": query.value(8),
        "margin_percent": query.value(9),
    }


def fetch_manufacturer_name(manufacturer_id):
    if manufacturer_id in (None, ""):
        return ""

    query = _new_query()
    query.prepare("SELECT name FROM manufacturer WHERE id = ? LIMIT 1")
    query.addBindValue(manufacturer_id)
    if not query.exec():
        raise Exception(f"Failed to load manufacturer name: {query.lastError().text()}")
    if query.next():
        return str(query.value(0) or "").strip()
    return ""


def fetch_recent_product_batch_rows(*, limit=5):
    query = _new_query()
    query.prepare(
        f"""
        SELECT
            b.id,
            p.id,
            p.display_name,
            COALESCE(m.name, '-'),
            COALESCE(b.batch_no, '-'),
            b.expiry_date,
            b.total_received,
            COALESCE((
                SELECT pp.pack_size
                FROM price_pack pp
                WHERE pp.product_id = p.id
                ORDER BY pp.is_default DESC, pp.id DESC
                LIMIT 1
            ), ''),
            COALESCE((
                SELECT pp.pack_price
                FROM price_pack pp
                WHERE pp.product_id = p.id
                ORDER BY pp.is_default DESC, pp.id DESC
                LIMIT 1
            ), 0)
        FROM batch b
        JOIN product p ON p.id = b.product_id
        LEFT JOIN manufacturer m ON m.id = p.manufacturer_id
        ORDER BY b.id DESC
        LIMIT {int(limit)}
        """
    )

    rows = []
    if not query.exec():
        raise Exception(f"Failed to load recent product batches: {query.lastError().text()}")

    while query.next():
        expiry_value = query.value(5)
        expiry_text = "-"
        if expiry_value:
            try:
                expiry_text = datetime.fromisoformat(str(expiry_value)).strftime("%m-%y")
            except Exception:
                expiry_text = str(expiry_value)

        rows.append(
            {
                "batch_id": int(query.value(0) or 0),
                "product_id": int(query.value(1) or 0),
                "product_name": str(query.value(2) or "-"),
                "manufacturer_name": str(query.value(3) or "-"),
                "batch_no": str(query.value(4) or "-"),
                "expiry_text": expiry_text,
                "quantity": float(query.value(6) or 0),
                "pack_size": str(query.value(7) or "-"),
                "pack_price": float(query.value(8) or 0.0),
            }
        )
    return rows


def fetch_product_detail_context(product_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            display_name,
            code,
            generic_name,
            brand,
            discount_group_id,
            tax_group_id,
            COALESCE(prescription_required, 0)
        FROM product
        WHERE id = ?
        """
    )
    query.addBindValue(int(product_id))

    if not query.exec():
        raise Exception(f"Failed to fetch product data: {query.lastError().text()}")
    if not query.next():
        return None

    stock_query = _new_query()
    stock_query.prepare(
        """
        SELECT COALESCE(SUM(quantity_remaining), 0) AS total_stock
        FROM batch
        WHERE product_id = ?
        """
    )
    stock_query.addBindValue(int(product_id))
    total_stock = 0
    if stock_query.exec() and stock_query.next():
        total_stock = stock_query.value(0) or 0

    price_query = _new_query()
    price_query.prepare(
        """
        SELECT pack_size, pack_price, unit_price
        FROM price_pack
        WHERE product_id = ?
        ORDER BY is_default DESC, id DESC
        LIMIT 1
        """
    )
    price_query.addBindValue(int(product_id))
    pack_size = "0"
    pack_price = "0"
    unit_price = "0"
    if price_query.exec() and price_query.next():
        pack_size = str(price_query.value(0))
        pack_price = str(price_query.value(1))
        unit_price = str(price_query.value(2))

    batch_query = _new_query()
    batch_query.prepare(
        """
        SELECT id, batch_no, expiry_date, total_received, quantity_remaining, unit_cost, source, received_at
        FROM batch
        WHERE product_id = ?
        ORDER BY expiry_date ASC
        """
    )
    batch_query.addBindValue(int(product_id))
    if not batch_query.exec():
        raise Exception(f"Failed to load product batches: {batch_query.lastError().text()}")

    batches = []
    while batch_query.next():
        batches.append(
            {
                "id": batch_query.value(0),
                "batch_no": batch_query.value(1),
                "expiry_date": batch_query.value(2),
                "total_received": batch_query.value(3),
                "quantity_remaining": batch_query.value(4),
                "unit_cost": batch_query.value(5),
                "source": batch_query.value(6),
                "received_at": batch_query.value(7),
            }
        )

    media_info = fetch_product_media(product_id)

    return {
        "header": {
            "display_name": query.value(0),
            "code": query.value(1),
            "generic_name": query.value(2),
            "brand": query.value(3),
            "discount_group_id": query.value(4),
            "tax_group_id": query.value(5),
            "prescription_required": bool(int(query.value(6) or 0)),
        },
        "stock": total_stock,
        "pricing": {
            "pack_size": pack_size,
            "pack_price": pack_price,
            "unit_price": unit_price,
        },
        "batches": batches,
        "media_info": media_info,
    }


def verify_active_admin_password(password: str) -> bool:
    normalized_password = str(password or "").strip()
    if not normalized_password:
        return False

    query = _new_query()
    query.prepare(
        """
        SELECT password_hash
        FROM auth
        WHERE role = 'admin'
          AND status = 'active'
        LIMIT 1
        """
    )

    if not query.exec():
        return False
    if not query.next():
        return False

    stored_hash = query.value(0)
    if not stored_hash:
        return False

    try:
        return bcrypt.checkpw(normalized_password.encode(), str(stored_hash).encode())
    except Exception:
        return False


def import_products_from_rows(rows):
    normalized_rows = list(rows or [])
    db = QSqlDatabase.database()
    if not db.transaction():
        raise Exception("Could not start transaction.")

    inserted_count = 0
    errors = []

    try:
        for row_index, row in enumerate(normalized_rows, start=1):
            try:
                reg_no = str(row.get("reg_no") or "").strip() or None
                brand = str(row.get("brand") or "").strip()
                generic_raw = str(row.get("generic") or "").strip()
                form = str(row.get("form") or "").strip() or None
                packing = str(row.get("packing") or "").strip() or None
                manufacturer_id = row.get("manufacturer_id")

                if not brand:
                    errors.append(f"Row {row_index}: Brand is required.")
                    continue

                generic_name = generic_raw
                strength = None
                if "[" in generic_raw and "]" in generic_raw:
                    generic_name = generic_raw.split("[", 1)[0].strip()
                    strength = generic_raw.split("[", 1)[1].split("]", 1)[0].strip() or None

                display_name = " ".join(
                    part.strip()
                    for part in [brand, form, strength]
                    if part and str(part).strip()
                )

                query = _new_query(db)
                query.prepare(
                    """
                    INSERT INTO product (
                        display_name,
                        code,
                        reg_no,
                        generic_name,
                        brand,
                        form,
                        strength,
                        packing,
                        rack,
                        manufacturer_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                )
                query.addBindValue(display_name)
                query.addBindValue(None)
                query.addBindValue(reg_no)
                query.addBindValue(generic_name or None)
                query.addBindValue(brand)
                query.addBindValue(form)
                query.addBindValue(strength)
                query.addBindValue(packing)
                query.addBindValue("")
                query.addBindValue(manufacturer_id)

                if not query.exec():
                    errors.append(f"Row {row_index}: {query.lastError().text()}")
                    continue

                inserted_count += 1
            except Exception as exc:
                errors.append(f"Row {row_index}: {str(exc)}")

        if errors:
            db.rollback()
            raise ValueError("\n".join(errors[:20]) + ("\n..." if len(errors) > 20 else ""))

        if not db.commit():
            db.rollback()
            raise Exception("Failed to commit import.")

        return inserted_count
    except Exception:
        if db.isOpen():
            db.rollback()
        raise


def _float_value(value, field_label, *, required=False, min_value=None, max_exclusive=None):
    text = str(value or "").strip()
    if not text:
        if required:
            raise ValueError(f"{field_label} is required.")
        return 0.0
    try:
        numeric = float(text)
    except Exception:
        raise ValueError(f"{field_label} must be a valid number.")
    if min_value is not None and numeric < min_value:
        raise ValueError(f"{field_label} must be at least {min_value}.")
    if max_exclusive is not None and numeric >= max_exclusive:
        raise ValueError(f"{field_label} must be less than {max_exclusive}.")
    return numeric


def parse_product_save_payload(
    *,
    existing_product_id,
    display_name,
    manufacturer_id,
    discount_group_id,
    tax_group_id,
    generic_name,
    code,
    rack,
    qty_text,
    batch_no,
    pack_size,
    pack_price_text,
    margin_text,
    reorder_level_text,
    expiry_date,
    form,
    strength,
    prescription_required,
):
    normalized_display_name = str(display_name or "").strip()
    if not normalized_display_name:
        raise ValueError("Product name is required.")

    quantity = _float_value(qty_text, "Quantity", required=True, min_value=0.0)
    pack_size_num = _float_value(pack_size, "Pack size", required=True, min_value=0.000001)
    pack_price = _float_value(pack_price_text, "Sale price", required=True, min_value=0.000001)

    margin_percent = DEFAULT_MARGIN_PERCENT
    if str(margin_text or "").strip():
        margin_percent = _float_value(margin_text, "Margin %", min_value=0.0, max_exclusive=100.0)

    reorder_level = 0.0
    if str(reorder_level_text or "").strip():
        reorder_level = _float_value(reorder_level_text, "Reorder level", min_value=0.0)

    return {
        "existing_product_id": existing_product_id,
        "display_name": normalized_display_name,
        "manufacturer_id": manufacturer_id,
        "discount_group_id": discount_group_id,
        "tax_group_id": tax_group_id,
        "generic_name": str(generic_name or "").strip() or None,
        "code": str(code or "").strip() or None,
        "rack": str(rack or "").strip(),
        "quantity": quantity,
        "batch_no": str(batch_no or "").strip() or None,
        "pack_size_text": str(pack_size or "").strip(),
        "pack_size_num": pack_size_num,
        "pack_price": pack_price,
        "margin_percent": margin_percent,
        "reorder_level": reorder_level,
        "expiry_date": expiry_date,
        "form": str(form or "").strip() or None,
        "strength": str(strength or "").strip(),
        "prescription_required": 1 if prescription_required else 0,
    }


def save_product_with_opening_stock(
    *,
    existing_product_id,
    display_name,
    manufacturer_id,
    discount_group_id,
    tax_group_id,
    generic_name,
    code,
    rack,
    qty_text,
    batch_no,
    pack_size,
    pack_price_text,
    margin_text,
    reorder_level_text,
    expiry_date,
    form,
    strength,
    prescription_required,
    media_removed=False,
    selected_media_path="",
):
    payload = parse_product_save_payload(
        existing_product_id=existing_product_id,
        display_name=display_name,
        manufacturer_id=manufacturer_id,
        discount_group_id=discount_group_id,
        tax_group_id=tax_group_id,
        generic_name=generic_name,
        code=code,
        rack=rack,
        qty_text=qty_text,
        batch_no=batch_no,
        pack_size=pack_size,
        pack_price_text=pack_price_text,
        margin_text=margin_text,
        reorder_level_text=reorder_level_text,
        expiry_date=expiry_date,
        form=form,
        strength=strength,
        prescription_required=prescription_required,
    )

    db = QSqlDatabase.database()
    if not db.transaction():
        raise Exception("Failed to start transaction.")

    try:
        created_new_product = False
        if payload["existing_product_id"] is not None:
            product_id = int(payload["existing_product_id"])
        else:
            brand_name = payload["display_name"]
            product_query = _new_query(db)
            product_query.prepare(
                """
                INSERT INTO product (
                    display_name,
                    code,
                    reg_no,
                    generic_name,
                    brand,
                    form,
                    strength,
                    packing,
                    rack,
                    manufacturer_id,
                    discount_group_id,
                    tax_group_id,
                    prescription_required,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
            )
            full_display_name = " ".join(
                part.strip()
                for part in [brand_name, payload["form"], payload["strength"]]
                if part and str(part).strip()
            )
            product_query.addBindValue(full_display_name)
            product_query.addBindValue(payload["code"])
            product_query.addBindValue("")
            product_query.addBindValue(payload["generic_name"])
            product_query.addBindValue(brand_name)
            product_query.addBindValue(payload["form"])
            product_query.addBindValue(payload["strength"])
            product_query.addBindValue("")
            product_query.addBindValue(payload["rack"])
            product_query.addBindValue(payload["manufacturer_id"])
            product_query.addBindValue(payload["discount_group_id"])
            product_query.addBindValue(payload["tax_group_id"])
            product_query.addBindValue(payload["prescription_required"])
            product_query.addBindValue("used")
            if not product_query.exec():
                raise Exception(product_query.lastError().text())
            product_id = int(product_query.lastInsertId())
            created_new_product = True

        status_query = _new_query(db)
        status_query.prepare(
            """
            UPDATE product
            SET
                status = 'used',
                code = ?,
                generic_name = ?,
                manufacturer_id = ?,
                discount_group_id = ?,
                tax_group_id = ?,
                rack = ?,
                prescription_required = ?
            WHERE id = ?
            """
        )
        status_query.addBindValue(payload["code"])
        status_query.addBindValue(payload["generic_name"])
        status_query.addBindValue(payload["manufacturer_id"])
        status_query.addBindValue(payload["discount_group_id"])
        status_query.addBindValue(payload["tax_group_id"])
        status_query.addBindValue(payload["rack"])
        status_query.addBindValue(payload["prescription_required"])
        status_query.addBindValue(product_id)
        if not status_query.exec():
            raise Exception(status_query.lastError().text())

        pack_cost = payload["pack_price"] * (1 - (payload["margin_percent"] / 100.0))
        unit_cost = round(pack_cost / payload["pack_size_num"], 6) if payload["pack_size_num"] > 0 else None

        batch_query = _new_query(db)
        batch_query.prepare(
            """
            INSERT INTO batch (
                batch_no,
                expiry_date,
                product_id,
                total_received,
                paid_qty,
                quantity_remaining,
                unit_cost,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
        )
        batch_query.addBindValue(payload["batch_no"])
        batch_query.addBindValue(payload["expiry_date"])
        batch_query.addBindValue(product_id)
        batch_query.addBindValue(payload["quantity"])
        batch_query.addBindValue(payload["quantity"])
        batch_query.addBindValue(payload["quantity"])
        batch_query.addBindValue(unit_cost)
        batch_query.addBindValue("OPENING")
        if not batch_query.exec():
            raise Exception(batch_query.lastError().text())
        batch_id = int(batch_query.lastInsertId())

        default_price_pack_id = None
        existing_default_query = _new_query(db)
        existing_default_query.prepare(
            """
            SELECT id
            FROM price_pack
            WHERE product_id = ?
            ORDER BY is_default DESC, id DESC
            LIMIT 1
            """
        )
        existing_default_query.addBindValue(product_id)
        if not existing_default_query.exec():
            raise Exception(existing_default_query.lastError().text())
        if existing_default_query.next():
            default_price_pack_id = existing_default_query.value(0)

        if default_price_pack_id is not None:
            normalize_default_query = _new_query(db)
            normalize_default_query.prepare(
                """
                UPDATE price_pack
                SET is_default = 0
                WHERE product_id = ?
                  AND id <> ?
                """
            )
            normalize_default_query.addBindValue(product_id)
            normalize_default_query.addBindValue(default_price_pack_id)
            if not normalize_default_query.exec():
                raise Exception(normalize_default_query.lastError().text())

            price_query = _new_query(db)
            price_query.prepare(
                """
                UPDATE price_pack
                SET pack_size = ?, pack_price = ?, margin_percent = ?, reorder_level = ?, is_default = 1
                WHERE id = ?
                """
            )
            price_query.addBindValue(payload["pack_size_text"])
            price_query.addBindValue(payload["pack_price"])
            price_query.addBindValue(payload["margin_percent"])
            price_query.addBindValue(payload["reorder_level"])
            price_query.addBindValue(default_price_pack_id)
        else:
            price_query = _new_query(db)
            price_query.prepare(
                """
                INSERT INTO price_pack (product_id, pack_size, pack_price, margin_percent, reorder_level, is_default)
                VALUES (?, ?, ?, ?, ?, 1)
                """
            )
            price_query.addBindValue(product_id)
            price_query.addBindValue(payload["pack_size_text"])
            price_query.addBindValue(payload["pack_price"])
            price_query.addBindValue(payload["margin_percent"])
            price_query.addBindValue(payload["reorder_level"])
        if not price_query.exec():
            raise Exception(price_query.lastError().text())

        saved_media_info = None
        if media_removed:
            clear_product_media_fields(product_id=product_id)
        elif str(selected_media_path or "").strip():
            saved_media_info = save_product_media(selected_media_path, product_id=product_id)
            update_product_media_fields(product_id=product_id, media_info=saved_media_info)

        if not db.commit():
            raise Exception("Transaction commit failed.")

        return {
            "product_id": product_id,
            "batch_id": batch_id,
            "created_new_product": created_new_product,
            "media_info": saved_media_info,
        }
    except Exception:
        db.rollback()
        raise


def update_product_detail_record(
    *,
    product_id,
    product_name,
    code,
    brand,
    formula,
    packsize,
    sale_price,
    discount_group_id,
    tax_group_id,
    prescription_required,
    media_removed=False,
    selected_media_path="",
    audit_source="product_detail",
    audit_user_id=None,
    audit_username="",
):
    normalized_product_name = str(product_name or "").strip()
    if not normalized_product_name:
        raise ValueError("Product name is required.")

    normalized_packsize = _float_value(packsize, "Pack size", required=True, min_value=0.000001)
    normalized_sale_price = _float_value(sale_price, "Sale price", required=True, min_value=0.000001)

    db = QSqlDatabase.database()
    if not db.transaction():
        raise Exception("Failed to start database transaction")

    try:
        old_price_query = _new_query(db)
        old_price_query.prepare(
            """
            SELECT pack_price
            FROM price_pack
            WHERE product_id = ?
            ORDER BY is_default DESC, id DESC
            LIMIT 1
            """
        )
        old_price_query.addBindValue(int(product_id))
        old_pack_price = None
        if old_price_query.exec() and old_price_query.next():
            old_pack_price = float(old_price_query.value(0) or 0.0)

        product_query = _new_query(db)
        product_query.prepare(
            """
            UPDATE product
            SET display_name = ?, code = ?, brand = ?, generic_name = ?, discount_group_id = ?, tax_group_id = ?, prescription_required = ?
            WHERE id = ?
            """
        )
        product_query.addBindValue(normalized_product_name)
        product_query.addBindValue(str(code or "").strip() or None)
        product_query.addBindValue(str(brand or "").strip())
        product_query.addBindValue(str(formula or "").strip())
        product_query.addBindValue(discount_group_id)
        product_query.addBindValue(tax_group_id)
        product_query.addBindValue(1 if prescription_required else 0)
        product_query.addBindValue(int(product_id))
        if not product_query.exec():
            raise Exception(f"Product update failed: {product_query.lastError().text()}")

        pricing_query = _new_query(db)
        pricing_query.prepare(
            """
            UPDATE price_pack
            SET pack_size = ?, pack_price = ?
            WHERE product_id = ?
            """
        )
        pricing_query.addBindValue(int(normalized_packsize) if normalized_packsize.is_integer() else normalized_packsize)
        pricing_query.addBindValue(normalized_sale_price)
        pricing_query.addBindValue(int(product_id))
        if not pricing_query.exec():
            raise Exception(f"Stock update failed: {pricing_query.lastError().text()}")
        if pricing_query.numRowsAffected() == 0:
            raise Exception("No stock rows were updated. Invalid product_id link ?")

        saved_media_info = None
        if media_removed:
            clear_product_media_fields(product_id=product_id)
        elif str(selected_media_path or "").strip():
            saved_media_info = save_product_media(selected_media_path, product_id=product_id)
            update_product_media_fields(product_id=product_id, media_info=saved_media_info)

        price_changed = old_pack_price is not None and old_pack_price != normalized_sale_price
        if price_changed:
            insert_price_change_log(
                product_id,
                old_pack_price,
                normalized_sale_price,
                source=audit_source,
                user_id=audit_user_id,
                username=audit_username,
            )

        if not db.commit():
            raise Exception(f"Commit failed: {db.lastError().text()}")

        return {
            "price_changed": price_changed,
            "old_pack_price": old_pack_price,
            "new_pack_price": normalized_sale_price,
            "media_info": saved_media_info,
        }
    except Exception:
        db.rollback()
        raise
