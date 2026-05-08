from PySide6.QtSql import QSqlQuery


def _new_query():
    return QSqlQuery()


def validate_salesrep_payload(*, supplier_id, name, contact):
    normalized_name = str(name or "").strip()
    normalized_contact = str(contact or "").strip()

    try:
        normalized_supplier_id = int(supplier_id or 0)
    except (TypeError, ValueError):
        normalized_supplier_id = 0

    if normalized_supplier_id <= 0:
        raise ValueError("Please select a supplier.")
    if not normalized_name:
        raise ValueError("Rep name is required.")
    if not normalized_contact:
        raise ValueError("Contact is required.")

    return {
        "supplier_id": normalized_supplier_id,
        "name": normalized_name,
        "contact": normalized_contact,
    }


def fetch_active_supplier_option_rows():
    query = _new_query()
    if not query.exec(
        "SELECT id, COALESCE(name, '') FROM supplier WHERE status = 'active' ORDER BY name ASC"
    ):
        raise Exception(f"Error loading suppliers: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "supplier_id": int(query.value(0) or 0),
                "supplier_name": str(query.value(1) or ""),
            }
        )
    return rows


def fetch_salesrep_option_rows_for_supplier(supplier_id):
    try:
        normalized_supplier_id = int(supplier_id or 0)
    except (TypeError, ValueError):
        normalized_supplier_id = 0

    if normalized_supplier_id <= 0:
        return []

    query = _new_query()
    query.prepare(
        """
        SELECT id, COALESCE(name, '')
        FROM rep
        WHERE supplier_id = ?
        ORDER BY name ASC
        """
    )
    query.addBindValue(normalized_supplier_id)

    if not query.exec():
        raise Exception(f"Error loading reps: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "rep_id": int(query.value(0) or 0),
                "rep_name": str(query.value(1) or "").strip(),
            }
        )
    return rows


def create_salesrep(*, supplier_id, name, contact):
    payload = validate_salesrep_payload(
        supplier_id=supplier_id,
        name=name,
        contact=contact,
    )
    query = _new_query()
    query.prepare(
        """
        INSERT INTO rep (supplier_id, name, contact)
        VALUES (?, ?, ?)
        """
    )
    query.addBindValue(payload["supplier_id"])
    query.addBindValue(payload["name"])
    query.addBindValue(payload["contact"])

    if not query.exec():
        raise Exception(f"Failed to save sales rep: {query.lastError().text()}")

    return query.lastInsertId()


def fetch_salesrep_list_rows():
    query = _new_query()
    query.prepare(
        """
        SELECT
            r.id,
            COALESCE(r.name, ''),
            COALESCE(s.name, 'Unknown'),
            COALESCE(r.contact, ''),
            COALESCE(r.status, '')
        FROM rep r
        LEFT JOIN supplier s ON s.id = r.supplier_id
        ORDER BY r.id ASC
        """
    )

    if not query.exec():
        raise Exception(f"Error loading sales reps: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "id": int(query.value(0) or 0),
                "name": str(query.value(1) or ""),
                "supplier_name": str(query.value(2) or "Unknown"),
                "contact": str(query.value(3) or ""),
                "status": str(query.value(4) or ""),
            }
        )
    return rows


def fetch_salesrep_detail(rep_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            COALESCE(r.name, ''),
            COALESCE(s.name, 'Unknown'),
            COALESCE(r.contact, ''),
            COALESCE(r.status, ''),
            r.joining_date
        FROM rep r
        LEFT JOIN supplier s ON s.id = r.supplier_id
        WHERE r.id = ?
        LIMIT 1
        """
    )
    query.addBindValue(int(rep_id))

    if not query.exec() or not query.next():
        raise Exception("Could not load sales rep detail.")

    return {
        "name": str(query.value(0) or ""),
        "supplier_name": str(query.value(1) or "Unknown"),
        "contact": str(query.value(2) or ""),
        "status": str(query.value(3) or ""),
        "joining_date": query.value(4),
    }


def update_salesrep(*, rep_id, name, contact, status):
    normalized_name = str(name or "").strip()
    normalized_contact = str(contact or "").strip()
    normalized_status = str(status or "").strip()

    if not normalized_name:
        raise ValueError("Rep name is required.")
    if not normalized_contact:
        raise ValueError("Contact is required.")
    if normalized_status not in {"Active", "Inactive"}:
        raise ValueError("Status must be Active or Inactive.")

    query = _new_query()
    query.prepare(
        """
        UPDATE rep
        SET name = ?, contact = ?, status = ?
        WHERE id = ?
        """
    )
    query.addBindValue(normalized_name)
    query.addBindValue(normalized_contact)
    query.addBindValue(normalized_status)
    query.addBindValue(int(rep_id))

    if not query.exec():
        raise Exception(f"Failed to update sales rep: {query.lastError().text()}")

    return True
