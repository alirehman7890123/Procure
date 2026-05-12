from PySide6.QtCore import QDate, QDateTime
from PySide6.QtSql import QSqlQuery


def _new_query():
    return QSqlQuery()


def validate_expense_payload(*, category, title, amount, note=""):
    category = str(category or "").strip()
    title = str(title or "").strip()
    note = str(note or "")

    if not category:
        raise ValueError("Category is required.")
    if not title:
        raise ValueError("Title is required.")

    amount_text = str(amount or "").strip()
    if not amount_text:
        raise ValueError("Amount is required.")

    try:
        amount_value = float(amount_text)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a valid number.")

    if amount_value < 0:
        raise ValueError("Amount cannot be negative.")

    return {
        "category": category,
        "title": title,
        "amount": amount_value,
        "note": note,
    }


def resolve_user_id(*, username=None, user_id=None):
    if user_id not in (None, "", 0):
        try:
            return int(user_id)
        except (TypeError, ValueError):
            pass

    username = str(username or "").strip()
    if not username:
        raise Exception("User not found in database.")

    query = _new_query()
    query.prepare("SELECT id FROM auth WHERE username = ?")
    query.addBindValue(username)

    if not query.exec():
        raise Exception(f"Could not resolve current user.\n\n{query.lastError().text()}")

    if not query.next():
        raise Exception("User not found in database.")

    return int(query.value(0) or 0)


def create_expense(
    *,
    category,
    title,
    amount,
    note="",
    session_id,
    username=None,
    user_id=None,
    payment_data=None,
):
    payload = validate_expense_payload(
        category=category,
        title=title,
        amount=amount,
        note=note,
    )

    if session_id in (None, "", 0):
        raise Exception("No active session found.")

    resolved_user_id = resolve_user_id(username=username, user_id=user_id)
    payment = dict(payment_data or {})

    query = _new_query()
    query.prepare(
        """
        INSERT INTO expense (
            category,
            title,
            amount,
            note,
            session_id,
            user_id,
            payment_method,
            bank_name,
            account_no,
            transaction_mode,
            wallet_provider,
            wallet_no,
            payment_reference
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(payload["category"])
    query.addBindValue(payload["title"])
    query.addBindValue(payload["amount"])
    query.addBindValue(payload["note"])
    query.addBindValue(int(session_id))
    query.addBindValue(int(resolved_user_id))
    query.addBindValue(payment.get("payment_method") or None)
    query.addBindValue(payment.get("bank_name") or None)
    query.addBindValue(payment.get("account_no") or None)
    query.addBindValue(payment.get("transaction_mode") or None)
    query.addBindValue(payment.get("wallet_provider") or None)
    query.addBindValue(payment.get("wallet_no") or None)
    query.addBindValue(payment.get("payment_reference") or None)

    if not query.exec():
        raise Exception(f"Could not add expense.\n\n{query.lastError().text()}")


def fetch_expense_list_rows():
    query = _new_query()
    query.prepare(
        """
        SELECT id, category, title, amount, creation_date
        FROM expense
        ORDER BY id DESC
        """
    )

    if not query.exec():
        raise Exception(f"Could not load expenses.\n\n{query.lastError().text()}")

    rows = []
    while query.next():
        creation_date_value = query.value(4)
        if isinstance(creation_date_value, QDateTime):
            creation_date_text = creation_date_value.toString("dd-MM-yyyy")
        elif isinstance(creation_date_value, QDate):
            creation_date_text = creation_date_value.toString("dd-MM-yyyy")
        else:
            creation_date_text = str(creation_date_value or "")

        try:
            amount_text = f"{float(query.value(3) or 0.0):.2f}"
        except (TypeError, ValueError):
            amount_text = "0.00"

        rows.append({
            "id": int(query.value(0) or 0),
            "category": str(query.value(1) or ""),
            "title": str(query.value(2) or ""),
            "amount_text": amount_text,
            "creation_date_text": creation_date_text,
        })
    return rows


def fetch_expense_detail(expense_id):
    query = _new_query()
    query.prepare(
        """
        SELECT
            e.category,
            e.title,
            e.amount,
            e.note,
            e.creation_date,
            e.payment_method,
            e.bank_name,
            e.account_no,
            e.transaction_mode,
            e.wallet_provider,
            e.wallet_no,
            e.payment_reference,
            e.user_id,
            COALESCE(a.first_name, ''),
            COALESCE(a.last_name, '')
        FROM expense e
        LEFT JOIN auth a ON a.id = e.user_id
        WHERE e.id = ?
        """
    )
    query.addBindValue(int(expense_id))

    if not query.exec():
        raise Exception(f"Could not load expense.\n\n{query.lastError().text()}")

    if not query.next():
        return None

    creation_date_value = query.value(4)
    if isinstance(creation_date_value, QDateTime):
        creation_text = creation_date_value.toString("dd-MM-yyyy")
    elif isinstance(creation_date_value, QDate):
        creation_text = creation_date_value.toString("dd-MM-yyyy")
    else:
        creation_text = str(creation_date_value or "-")

    payment_text = build_payment_text(
        payment_method=str(query.value(5) or "").strip(),
        bank_name=str(query.value(6) or "").strip(),
        account_no=str(query.value(7) or "").strip(),
        transaction_mode=str(query.value(8) or "").strip(),
        wallet_provider=str(query.value(9) or "").strip(),
        wallet_no=str(query.value(10) or "").strip(),
        payment_reference=str(query.value(11) or "").strip(),
    )

    first_name = str(query.value(13) or "").strip()
    last_name = str(query.value(14) or "").strip()
    created_by_text = f"{first_name} {last_name}".strip() or "-"

    try:
        amount_text = f"{float(query.value(2) or 0.0):.2f}"
    except (TypeError, ValueError):
        amount_text = "0.00"

    return {
        "category": str(query.value(0) or "-"),
        "title": str(query.value(1) or "-"),
        "amount_text": amount_text,
        "note": str(query.value(3) or "-"),
        "creation_text": creation_text,
        "payment_text": payment_text,
        "created_by_text": created_by_text,
    }


def build_payment_text(
    *,
    payment_method,
    bank_name,
    account_no,
    transaction_mode,
    wallet_provider,
    wallet_no,
    payment_reference,
):
    payment_method = (payment_method or "").strip()
    bank_name = (bank_name or "").strip()
    account_no = (account_no or "").strip()
    transaction_mode = (transaction_mode or "").strip()
    wallet_provider = (wallet_provider or "").strip()
    wallet_no = (wallet_no or "").strip()
    payment_reference = (payment_reference or "").strip()

    if not payment_method:
        return "-"

    lines = [payment_method]

    if payment_method.lower() == "bank transfer":
        if transaction_mode:
            lines.append(f"Mode: {transaction_mode}")
        if bank_name:
            lines.append(f"Bank: {bank_name}")
        if account_no:
            lines.append(f"Account No: {account_no}")
    elif payment_method.lower() in {"easypaisa", "jazzcash"}:
        if wallet_provider:
            lines.append(f"Wallet: {wallet_provider}")
        if wallet_no:
            lines.append(f"Wallet No: {wallet_no}")

    if payment_reference:
        lines.append(f"Reference: {payment_reference}")

    return "\n".join(lines)
