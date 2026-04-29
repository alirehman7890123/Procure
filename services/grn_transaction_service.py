def _new_query():
    from PySide6.QtSql import QSqlQuery

    return QSqlQuery()


def insert_goods_receipt_header(payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO goods_receipt (
            grn_number,
            po_id,
            grn_date,
            status,
            total_value,
            header_discount,
            header_tax,
            discount,
            tax_236g,
            tax_236h,
            salestax,
            cn_adjustment,
            taxable,
            netamount,
            session_id,
            notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(payload["grn_number"])
    query.addBindValue(payload["po_id"])
    query.addBindValue(payload["grn_date"])
    query.addBindValue(payload["status"])
    query.addBindValue(payload["total_value"])
    query.addBindValue(payload["header_discount"])
    query.addBindValue(payload["header_tax"])
    query.addBindValue(payload["discount"])
    query.addBindValue(payload["tax_236g"])
    query.addBindValue(payload["tax_236h"])
    query.addBindValue(payload["salestax"])
    query.addBindValue(payload["cn_adjustment"])
    query.addBindValue(payload["taxable"])
    query.addBindValue(payload["netamount"])
    query.addBindValue(payload["session_id"])
    query.addBindValue(payload["notes"])

    if not query.exec():
        raise Exception(query.lastError().text())

    return int(query.lastInsertId())


def insert_goods_receipt_line(grn_id, line_payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO goods_receipt_line (
            grn_id, po_line_id, qty_received, unit_price_received, total_received,
            batch_no, expiry_date, discount, tax, landing_cost
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(grn_id)
    query.addBindValue(line_payload["po_line_id"])
    query.addBindValue(line_payload["qty_received"])
    query.addBindValue(line_payload["unit_price"])
    query.addBindValue(line_payload["total_received"])
    query.addBindValue(line_payload["batch_no"])
    query.addBindValue(line_payload["expiry_date"])
    query.addBindValue(line_payload["discount"])
    query.addBindValue(line_payload["tax"])
    query.addBindValue(line_payload["landing_cost"])

    if not query.exec():
        raise Exception(query.lastError().text())

    return int(query.lastInsertId())


def update_goods_receipt_status(grn_number, status):
    query = _new_query()
    query.prepare("UPDATE goods_receipt SET status = ? WHERE grn_number = ?")
    query.addBindValue(status)
    query.addBindValue(grn_number)
    if not query.exec():
        raise Exception(f"GRN status update failed: {query.lastError().text()}")
    return True


def fetch_grn_list_rows(*, date_from, date_to, search_text=""):
    normalized_search = str(search_text or "").strip()
    query = _new_query()

    sql = """
        SELECT
            gr.id,
            gr.grn_number,
            po.po_number,
            COALESCE(s.name, '') AS supplier_name,
            gr.grn_date,
            gr.status,
            COALESCE(gr.total_value, 0)
        FROM goods_receipt gr
        JOIN purchase_order po ON gr.po_id = po.id
        JOIN supplier s ON po.supplier = s.id
        WHERE gr.grn_date BETWEEN ? AND ?
    """
    params = [date_from, date_to]
    if normalized_search:
        sql += " AND (gr.grn_number LIKE ? OR po.po_number LIKE ? OR s.name LIKE ?)"
        wildcard = f"%{normalized_search}%"
        params.extend([wildcard, wildcard, wildcard])
    sql += " ORDER BY gr.id DESC"

    query.prepare(sql)
    for param in params:
        query.addBindValue(param)

    if not query.exec():
        raise Exception(f"GRN list load failed: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "grn_id": int(query.value(0) or 0),
                "grn_number": str(query.value(1) or ""),
                "po_number": str(query.value(2) or ""),
                "supplier_name": str(query.value(3) or ""),
                "grn_date": str(query.value(4) or ""),
                "status": str(query.value(5) or ""),
                "total_value": float(query.value(6) or 0.0),
            }
        )
    return rows


def fetch_grn_detail(grn_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            gr.grn_number,
            gr.grn_date,
            gr.status,
            COALESCE(gr.total_value, 0),
            po.po_number,
            COALESCE(s.name, '-') AS supplier_name,
            COALESCE(gr.session_id, ''),
            COALESCE(gr.header_discount, 0),
            COALESCE((
                SELECT SUM(COALESCE(grl.total_received, 0))
                FROM goods_receipt_line grl
                WHERE grl.grn_id = gr.id
            ), 0),
            COALESCE(gr.taxable, 0),
            COALESCE(gr.tax_236g, 0),
            COALESCE(gr.tax_236h, 0),
            COALESCE(gr.salestax, 0),
            COALESCE(gr.header_tax, 0),
            COALESCE(gr.netamount, 0),
            COALESCE(gr.cn_adjustment, 0),
            COALESCE(gr.notes, ''),
            COALESCE((SELECT MAX(p.id) FROM purchase p WHERE p.sellerinvoice = gr.grn_number), '') AS bill_id
        FROM goods_receipt gr
        JOIN purchase_order po ON gr.po_id = po.id
        JOIN supplier s ON po.supplier = s.id
        WHERE gr.id = ?
        LIMIT 1
        """
    )
    query.addBindValue(int(grn_id))

    if not query.exec():
        raise Exception("Could not load GRN details.")
    if not query.next():
        return None

    return {
        "grn_number": str(query.value(0) or "-"),
        "grn_date": str(query.value(1) or "-"),
        "status": str(query.value(2) or "-"),
        "total_value": float(query.value(3) or 0.0),
        "po_number": str(query.value(4) or "-"),
        "supplier_name": str(query.value(5) or "-"),
        "session_id": str(query.value(6) or "-"),
        "header_discount": float(query.value(7) or 0.0),
        "subtotal": float(query.value(8) or 0.0),
        "taxable": float(query.value(9) or 0.0),
        "tax_236g": float(query.value(10) or 0.0),
        "tax_236h": float(query.value(11) or 0.0),
        "sales_tax": float(query.value(12) or 0.0),
        "header_tax": float(query.value(13) or 0.0),
        "net_amount": float(query.value(14) or 0.0),
        "cn_adjustment": float(query.value(15) or 0.0),
        "notes": str(query.value(16) or ""),
        "bill_id": str(query.value(17) or ""),
    }


def fetch_grn_line_rows(grn_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            COALESCE(p.display_name, '') AS product_name,
            COALESCE(grl.batch_no, ''),
            COALESCE(grl.expiry_date, ''),
            COALESCE(grl.qty_received, 0),
            COALESCE(grl.unit_price_received, 0),
            COALESCE(grl.discount, 0),
            COALESCE(grl.tax, 0),
            COALESCE(grl.total_received, 0),
            COALESCE(grl.landing_cost, 0)
        FROM goods_receipt_line grl
        JOIN purchase_order_line pol ON grl.po_line_id = pol.id
        JOIN product p ON pol.product = p.id
        WHERE grl.grn_id = ?
        ORDER BY grl.id ASC
        """
    )
    query.addBindValue(int(grn_id))

    if not query.exec():
        raise Exception(f"Failed to load GRN lines: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "product_name": str(query.value(0) or ""),
                "batch_no": str(query.value(1) or ""),
                "expiry_date": str(query.value(2) or ""),
                "qty_received": int(float(query.value(3) or 0)),
                "unit_price_received": float(query.value(4) or 0.0),
                "discount": float(query.value(5) or 0.0),
                "tax": float(query.value(6) or 0.0),
                "total_received": float(query.value(7) or 0.0),
                "landing_cost": float(query.value(8) or 0.0),
            }
        )
    return rows


def fetch_grn_health_check_counts():
    checks = [
        (
            "GRN without lines",
            """
            SELECT COUNT(*)
            FROM goods_receipt gr
            WHERE NOT EXISTS (
                SELECT 1 FROM goods_receipt_line grl WHERE grl.grn_id = gr.id
            )
            """,
        ),
        (
            "Receipt lines with missing PO line",
            """
            SELECT COUNT(*)
            FROM goods_receipt_line grl
            LEFT JOIN purchase_order_line pol ON pol.id = grl.po_line_id
            WHERE pol.id IS NULL
            """,
        ),
        (
            "Billed GRNs missing purchase bill",
            """
            SELECT COUNT(*)
            FROM goods_receipt gr
            WHERE gr.status = 'billed'
              AND NOT EXISTS (
                SELECT 1 FROM purchase p WHERE p.sellerinvoice = gr.grn_number
              )
            """,
        ),
        (
            "GRN without stock batches",
            """
            SELECT COUNT(*)
            FROM goods_receipt gr
            WHERE EXISTS (
                SELECT 1 FROM goods_receipt_line grl WHERE grl.grn_id = gr.id
            )
              AND NOT EXISTS (
                SELECT 1
                FROM batch b
                LEFT JOIN purchaseitem pi ON pi.id = b.purchaseitem_id
                LEFT JOIN purchase p ON p.id = pi.purchase
                WHERE b.source = ('GRN:' || gr.grn_number)
                   OR p.sellerinvoice = gr.grn_number
              )
            """,
        ),
        (
            "PO status inconsistent with received quantity",
            """
            WITH po_totals AS (
                SELECT
                    po.id,
                    po.status,
                    COALESCE((SELECT SUM(qty_ordered) FROM purchase_order_line WHERE po_id = po.id), 0) AS ordered_qty,
                    COALESCE((
                        SELECT SUM(grl.qty_received)
                        FROM goods_receipt_line grl
                        JOIN goods_receipt gr ON gr.id = grl.grn_id
                        JOIN purchase_order_line pol ON pol.id = grl.po_line_id
                        WHERE gr.po_id = po.id
                    ), 0) AS received_qty
                FROM purchase_order po
                WHERE po.status != 'closed'
            )
            SELECT COUNT(*)
            FROM po_totals
            WHERE (
                received_qty <= 0 AND status NOT IN ('draft', 'sent')
            ) OR (
                received_qty > 0 AND received_qty < ordered_qty AND status != 'partial_received'
            ) OR (
                received_qty >= ordered_qty AND ordered_qty > 0 AND status != 'received'
            )
            """,
        ),
        (
            "GRN total not matching receipt + header adjustments",
            """
            SELECT COUNT(*)
            FROM goods_receipt gr
            LEFT JOIN (
                SELECT
                    grn_id,
                    ROUND(SUM(COALESCE(total_received, 0) - COALESCE(discount, 0) + COALESCE(tax, 0)), 2) AS lines_total
                FROM goods_receipt_line
                GROUP BY grn_id
            ) x ON x.grn_id = gr.id
            WHERE ABS(
                COALESCE(gr.total_value, 0) - (
                    COALESCE(x.lines_total, 0)
                    - COALESCE(gr.header_discount, 0)
                    + COALESCE(gr.tax_236g, 0)
                    + COALESCE(gr.tax_236h, 0)
                    + COALESCE(gr.salestax, 0)
                    - COALESCE(gr.cn_adjustment, 0)
                )
            ) > 0.01
            """,
        ),
    ]

    results = []
    for label, sql in checks:
        query = _new_query()
        if not query.exec(sql) or not query.next():
            results.append({"label": label, "count": None})
        else:
            results.append({"label": label, "count": int(query.value(0) or 0)})
    return results


def fetch_open_po_option_rows():
    query = _new_query()
    if not query.exec(
        """
        SELECT
            po.id,
            po.po_number
        FROM purchase_order po
        WHERE po.status IN ('draft', 'sent', 'partial_received')
          AND COALESCE((SELECT SUM(qty_ordered) FROM purchase_order_line WHERE po_id = po.id), 0) >
              COALESCE((
                  SELECT SUM(grl.qty_received)
                  FROM goods_receipt_line grl
                  JOIN purchase_order_line pol ON pol.id = grl.po_line_id
                  WHERE pol.po_id = po.id
              ), 0)
        ORDER BY po.id DESC
        """
    ):
        raise Exception(f"PO options load failed: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "po_id": int(query.value(0) or 0),
                "po_number": str(query.value(1) or ""),
            }
        )
    return rows


def fetch_po_supplier_rep_context(po_id):
    supplier_query = _new_query()
    supplier_query.prepare(
        """
        SELECT s.id, COALESCE(s.name, '')
        FROM purchase_order po
        JOIN supplier s ON po.supplier = s.id
        WHERE po.id = ?
        LIMIT 1
        """
    )
    supplier_query.addBindValue(int(po_id))

    if not supplier_query.exec() or not supplier_query.next():
        raise Exception("Could not resolve supplier for selected PO.")

    supplier_id = int(supplier_query.value(0) or 0)
    supplier_name = str(supplier_query.value(1) or "")

    rep_query = _new_query()
    rep_query.prepare(
        """
        SELECT id, COALESCE(name, '')
        FROM rep
        WHERE supplier_id = ?
        ORDER BY name
        """
    )
    rep_query.addBindValue(supplier_id)
    if not rep_query.exec():
        raise Exception(f"Failed to load reps: {rep_query.lastError().text()}")

    reps = []
    while rep_query.next():
        reps.append(
            {
                "rep_id": int(rep_query.value(0) or 0),
                "rep_name": str(rep_query.value(1) or ""),
            }
        )

    return {
        "supplier_id": supplier_id,
        "supplier_name": supplier_name,
        "reps": reps,
    }


def fetch_po_receipt_line_rows(po_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            pol.id,
            pol.product,
            COALESCE(p.display_name, '') AS product_name,
            COALESCE(pol.qty_ordered, 0),
            COALESCE(pol.unit_price, 0),
            COALESCE(SUM(grl.qty_received), 0) AS qty_prev_received
        FROM purchase_order_line pol
        JOIN product p ON pol.product = p.id
        LEFT JOIN goods_receipt_line grl ON grl.po_line_id = pol.id
        WHERE pol.po_id = ?
        GROUP BY pol.id, pol.product, p.display_name, pol.qty_ordered, pol.unit_price
        ORDER BY pol.id ASC
        """
    )
    query.addBindValue(int(po_id))

    if not query.exec():
        raise Exception(f"PO lines load failed: {query.lastError().text()}")

    rows = []
    while query.next():
        qty_ordered = int(query.value(3) or 0)
        qty_prev_received = int(query.value(5) or 0)
        qty_remaining = max(qty_ordered - qty_prev_received, 0)
        if qty_remaining <= 0:
            continue
        rows.append(
            {
                "po_line_id": int(query.value(0) or 0),
                "product_id": int(query.value(1) or 0),
                "product_name": str(query.value(2) or ""),
                "qty_ordered": qty_ordered,
                "unit_price": float(query.value(4) or 0.0),
                "qty_prev_received": qty_prev_received,
                "qty_remaining": qty_remaining,
            }
        )
    return rows


def resolve_po_supplier_id(po_id):
    context = fetch_po_supplier_rep_context(po_id)
    return int(context["supplier_id"] or 0)


def recompute_po_status_from_receipts(po_id):
    status_query = _new_query()
    status_query.prepare("SELECT status, po_number FROM purchase_order WHERE id = ?")
    status_query.addBindValue(int(po_id))
    if not status_query.exec() or not status_query.next():
        raise Exception("Could not read current PO status.")

    current_status = str(status_query.value(0) or "")
    po_number = str(status_query.value(1) or "")
    if current_status == "closed":
        return current_status

    totals_query = _new_query()
    totals_query.prepare(
        """
        SELECT
            COALESCE((SELECT SUM(qty_ordered) FROM purchase_order_line WHERE po_id = ?), 0),
            COALESCE((
                SELECT SUM(grl.qty_received)
                FROM goods_receipt_line grl
                JOIN goods_receipt gr ON gr.id = grl.grn_id
                JOIN purchase_order_line pol ON pol.id = grl.po_line_id
                WHERE gr.po_id = ?
            ), 0)
        """
    )
    totals_query.addBindValue(int(po_id))
    totals_query.addBindValue(int(po_id))
    if not totals_query.exec() or not totals_query.next():
        raise Exception("Could not compute PO receipt totals.")

    ordered_total = float(totals_query.value(0) or 0.0)
    received_total = float(totals_query.value(1) or 0.0)

    new_status = current_status
    if ordered_total > 0:
        if received_total <= 0:
            new_status = "sent"
        elif received_total < ordered_total:
            new_status = "partial_received"
        else:
            new_status = "received"

    if new_status != current_status:
        update_query = _new_query()
        update_query.prepare("UPDATE purchase_order SET status = ? WHERE id = ?")
        update_query.addBindValue(new_status)
        update_query.addBindValue(int(po_id))
        if not update_query.exec():
            raise Exception(f"PO status update failed: {update_query.lastError().text()}")

    return new_status


def fetch_next_grn_number():
    query = _new_query()
    if not query.exec(
        """
        SELECT MAX(CAST(SUBSTR(grn_number, 5) AS INTEGER))
        FROM goods_receipt
        WHERE grn_number LIKE 'GRN-%'
        """
    ):
        return "GRN-1001"

    next_no = 1001
    if query.next() and query.value(0) is not None:
        try:
            next_no = max(int(query.value(0)) + 1, 1001)
        except (TypeError, ValueError):
            next_no = 1001

    return f"GRN-{next_no}"
