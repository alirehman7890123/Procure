"""
payroll_service.py — Pure DB query functions for the payroll module.
No UI imports. All functions operate via QSqlQuery.
"""

from PySide6.QtSql import QSqlQuery

from medic.services.db_transaction_service import run_in_transaction

# ---------------------------------------------------------------------------
# Employee helpers
# ---------------------------------------------------------------------------

def get_all_active_employees():
    """Return list of dicts: id, name, basic_salary, advance_balance."""
    query = QSqlQuery()
    query.prepare("""
        SELECT id, name, basic_salary, advance_balance
        FROM employee
        WHERE status = 'active'
        ORDER BY name ASC
    """)
    query.exec()
    results = []
    while query.next():
        results.append({
            "id": query.value(0),
            "name": query.value(1),
            "basic_salary": query.value(2) or 0.0,
            "advance_balance": query.value(3) or 0.0,
        })
    return results


def get_employee_by_id(employee_id):
    """Return single employee dict or None."""
    query = QSqlQuery()
    query.prepare("""
        SELECT id, name, basic_salary, advance_balance, role, contact
        FROM employee WHERE id = ?
    """)
    query.addBindValue(employee_id)
    query.exec()
    if query.next():
        return {
            "id": query.value(0),
            "name": query.value(1),
            "basic_salary": query.value(2) or 0.0,
            "advance_balance": query.value(3) or 0.0,
            "role": query.value(4),
            "contact": query.value(5),
        }
    return None


def resolve_payroll_auth_user_id(username):
    """Resolve an auth user id from username for payroll recording flows."""
    query = QSqlQuery()
    query.prepare("SELECT id FROM auth WHERE username = ? LIMIT 1")
    query.addBindValue(username)
    query.exec()
    return query.value(0) if query.next() else None


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------

def get_attendance_for_month(employee_id, year_month):
    """
    Return list of dicts for a given employee and month (YYYY-MM).
    Each dict: date, status, check_in, check_out, notes
    """
    query = QSqlQuery()
    query.prepare("""
        SELECT date, status, check_in, check_out, notes
        FROM attendance
        WHERE employee_id = ? AND date LIKE ?
        ORDER BY date ASC
    """)
    query.addBindValue(employee_id)
    query.addBindValue(f"{year_month}-%")
    query.exec()
    results = []
    while query.next():
        results.append({
            "date": query.value(0),
            "status": query.value(1),
            "check_in": query.value(2),
            "check_out": query.value(3),
            "notes": query.value(4),
        })
    return results


def get_attendance_summary(employee_id, year_month):
    """
    Return dict: present, absent, half_day, leave counts for the given month.
    """
    query = QSqlQuery()
    query.prepare("""
        SELECT
            SUM(CASE WHEN status = 'present'  THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'absent'   THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'half_day' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'leave'    THEN 1 ELSE 0 END)
        FROM attendance
        WHERE employee_id = ? AND date LIKE ?
    """)
    query.addBindValue(employee_id)
    query.addBindValue(f"{year_month}-%")
    query.exec()
    if query.next():
        return {
            "present":  query.value(0) or 0,
            "absent":   query.value(1) or 0,
            "half_day": query.value(2) or 0,
            "leave":    query.value(3) or 0,
        }
    return {"present": 0, "absent": 0, "half_day": 0, "leave": 0}


def get_attendance_record(employee_id, date):
    """Return a single attendance record dict or None."""
    query = QSqlQuery()
    query.prepare("""
        SELECT id, status, check_in, check_out, notes
        FROM attendance WHERE employee_id = ? AND date = ?
    """)
    query.addBindValue(employee_id)
    query.addBindValue(date)
    query.exec()
    if query.next():
        return {
            "id": query.value(0),
            "status": query.value(1),
            "check_in": query.value(2),
            "check_out": query.value(3),
            "notes": query.value(4),
        }
    return None


def upsert_attendance(employee_id, date, status, check_in, check_out, notes,
                      session_id, recorded_by):
    """Insert or replace attendance for employee+date. Returns True on success."""
    query = QSqlQuery()
    query.prepare("""
        INSERT INTO attendance (employee_id, date, status, check_in, check_out,
                                notes, session_id, recorded_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(employee_id, date) DO UPDATE SET
            status      = excluded.status,
            check_in    = excluded.check_in,
            check_out   = excluded.check_out,
            notes       = excluded.notes,
            session_id  = excluded.session_id,
            recorded_by = excluded.recorded_by
    """)
    query.addBindValue(employee_id)
    query.addBindValue(date)
    query.addBindValue(status)
    query.addBindValue(check_in or None)
    query.addBindValue(check_out or None)
    query.addBindValue(notes or None)
    query.addBindValue(session_id)
    query.addBindValue(recorded_by)
    return query.exec()


def get_monthly_attendance_all_employees(year_month):
    """
    Return a list of dicts for ALL employees and their monthly attendance counts.
    Used in the attendance list view.
    """
    query = QSqlQuery()
    query.prepare("""
        SELECT
            e.id,
            e.name,
            SUM(CASE WHEN a.status = 'present'  THEN 1 ELSE 0 END) AS present,
            SUM(CASE WHEN a.status = 'absent'   THEN 1 ELSE 0 END) AS absent,
            SUM(CASE WHEN a.status = 'half_day' THEN 1 ELSE 0 END) AS half_day,
            SUM(CASE WHEN a.status = 'leave'    THEN 1 ELSE 0 END) AS leave,
            COUNT(a.id) AS total_marked
        FROM employee e
        LEFT JOIN attendance a ON a.employee_id = e.id AND a.date LIKE ?
        WHERE e.status = 'active'
        GROUP BY e.id, e.name
        ORDER BY e.name ASC
    """)
    query.addBindValue(f"{year_month}-%")
    query.exec()
    results = []
    while query.next():
        results.append({
            "id":           query.value(0),
            "name":         query.value(1),
            "present":      query.value(2) or 0,
            "absent":       query.value(3) or 0,
            "half_day":     query.value(4) or 0,
            "leave":        query.value(5) or 0,
            "total_marked": query.value(6) or 0,
        })
    return results


# ---------------------------------------------------------------------------
# Salary Advance
# ---------------------------------------------------------------------------

def get_pending_advances(employee_id):
    """Return list of unrecovered/partial advances for an employee."""
    query = QSqlQuery()
    query.prepare("""
        SELECT id, amount, recovered, reason, date, status
        FROM salary_advance
        WHERE employee_id = ? AND status IN ('pending', 'partial')
        ORDER BY date ASC
    """)
    query.addBindValue(employee_id)
    query.exec()
    results = []
    while query.next():
        results.append({
            "id":        query.value(0),
            "amount":    query.value(1) or 0.0,
            "recovered": query.value(2) or 0.0,
            "reason":    query.value(3),
            "date":      query.value(4),
            "status":    query.value(5),
        })
    return results


def get_all_advances(employee_id=None):
    """Return all advances, optionally filtered by employee."""
    query = QSqlQuery()
    if employee_id:
        query.prepare("""
            SELECT sa.id, e.name, sa.amount, sa.recovered, sa.reason,
                   sa.date, sa.status
            FROM salary_advance sa
            JOIN employee e ON e.id = sa.employee_id
            WHERE sa.employee_id = ?
            ORDER BY sa.date DESC
        """)
        query.addBindValue(employee_id)
    else:
        query.prepare("""
            SELECT sa.id, e.name, sa.amount, sa.recovered, sa.reason,
                   sa.date, sa.status
            FROM salary_advance sa
            JOIN employee e ON e.id = sa.employee_id
            ORDER BY sa.date DESC
        """)
    query.exec()
    results = []
    while query.next():
        results.append({
            "id":        query.value(0),
            "emp_name":  query.value(1),
            "amount":    query.value(2) or 0.0,
            "recovered": query.value(3) or 0.0,
            "reason":    query.value(4),
            "date":      query.value(5),
            "status":    query.value(6),
        })
    return results


def insert_salary_advance(employee_id, amount, reason, date, session_id, recorded_by):
    """Insert a new salary advance record. Returns (True, last_insert_id) or (False, error)."""
    query = QSqlQuery()
    query.prepare("""
        INSERT INTO salary_advance (employee_id, amount, reason, date, session_id, recorded_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """)
    query.addBindValue(employee_id)
    query.addBindValue(amount)
    query.addBindValue(reason or None)
    query.addBindValue(date)
    query.addBindValue(session_id)
    query.addBindValue(recorded_by)
    if query.exec():
        return True, query.lastInsertId()
    return False, query.lastError().text()


def update_employee_advance_balance(conn_or_query, employee_id, delta):
    """Add delta to employee.advance_balance (use positive for new advance, negative for recovery)."""
    query = QSqlQuery()
    query.prepare("""
        UPDATE employee SET advance_balance = COALESCE(advance_balance, 0) + ?
        WHERE id = ?
    """)
    query.addBindValue(delta)
    query.addBindValue(employee_id)
    return query.exec()


def save_salary_advance_entry(*, employee_id, amount, reason, date, session_id, recorded_by):
    def _work():
        ok, result = insert_salary_advance(
            employee_id=employee_id,
            amount=amount,
            reason=reason,
            date=date,
            session_id=session_id,
            recorded_by=recorded_by,
        )
        if not ok:
            raise Exception(result)
        if not update_employee_advance_balance(None, employee_id, amount):
            raise Exception("Failed to update employee advance balance.")
        return result

    return run_in_transaction(
        _work,
        start_error_message="Could not start salary advance transaction.",
        commit_error_message="Could not commit salary advance transaction.",
    )


# ---------------------------------------------------------------------------
# Payroll
# ---------------------------------------------------------------------------

def get_payroll_list(employee_id=None, year_month=None):
    """Return list of payroll slips, optionally filtered."""
    conditions = []
    binds = []

    if employee_id:
        conditions.append("p.employee_id = ?")
        binds.append(employee_id)
    if year_month:
        conditions.append("p.month = ?")
        binds.append(year_month)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = QSqlQuery()
    query.prepare(f"""
        SELECT p.id, e.name, p.month, p.basic_salary, p.allowances,
               p.deductions, p.advance_deduct, p.net_salary,
               p.payment_method, p.status, p.paid_on
        FROM payroll p
        JOIN employee e ON e.id = p.employee_id
        {where}
        ORDER BY p.month DESC, e.name ASC
    """)
    for b in binds:
        query.addBindValue(b)
    query.exec()
    results = []
    while query.next():
        results.append({
            "id":             query.value(0),
            "emp_name":       query.value(1),
            "month":          query.value(2),
            "basic_salary":   query.value(3) or 0.0,
            "allowances":     query.value(4) or 0.0,
            "deductions":     query.value(5) or 0.0,
            "advance_deduct": query.value(6) or 0.0,
            "net_salary":     query.value(7) or 0.0,
            "payment_method": query.value(8),
            "status":         query.value(9),
            "paid_on":        query.value(10),
        })
    return results


def get_payroll_detail(payroll_id):
    """Return full payroll detail dict or None."""
    query = QSqlQuery()
    query.prepare("""
        SELECT p.id, e.name, e.role, e.contact,
               p.month, p.basic_salary, p.allowances,
               p.deductions, p.advance_deduct, p.net_salary,
               p.payment_method, p.bank_name, p.account_no,
               p.transaction_mode, p.wallet_provider, p.wallet_no,
               p.payment_reference, p.status, p.notes, p.paid_on,
               a.username AS paid_by
        FROM payroll p
        JOIN employee e ON e.id = p.employee_id
        LEFT JOIN auth a ON a.id = p.paid_by
        WHERE p.id = ?
    """)
    query.addBindValue(payroll_id)
    query.exec()
    if query.next():
        return {
            "id":               query.value(0),
            "emp_name":         query.value(1),
            "emp_role":         query.value(2),
            "emp_contact":      query.value(3),
            "month":            query.value(4),
            "basic_salary":     query.value(5) or 0.0,
            "allowances":       query.value(6) or 0.0,
            "deductions":       query.value(7) or 0.0,
            "advance_deduct":   query.value(8) or 0.0,
            "net_salary":       query.value(9) or 0.0,
            "payment_method":   query.value(10),
            "bank_name":        query.value(11),
            "account_no":       query.value(12),
            "transaction_mode": query.value(13),
            "wallet_provider":  query.value(14),
            "wallet_no":        query.value(15),
            "payment_reference":query.value(16),
            "status":           query.value(17),
            "notes":            query.value(18),
            "paid_on":          query.value(19),
            "paid_by":          query.value(20),
        }
    return None


def payroll_exists(employee_id, year_month):
    """Return True if a payroll slip already exists for employee+month."""
    query = QSqlQuery()
    query.prepare("SELECT id FROM payroll WHERE employee_id = ? AND month = ?")
    query.addBindValue(employee_id)
    query.addBindValue(year_month)
    query.exec()
    return query.next()


def insert_payroll(employee_id, month, basic_salary, allowances, deductions,
                   advance_deduct, net_salary, payment_data, notes, paid_on,
                   session_id, paid_by):
    """Insert a payroll slip. Returns (True, id) or (False, error_text)."""
    query = QSqlQuery()
    query.prepare("""
        INSERT INTO payroll (
            employee_id, month, basic_salary, allowances, deductions,
            advance_deduct, net_salary,
            payment_method, bank_name, account_no, transaction_mode,
            wallet_provider, wallet_no, payment_reference,
            status, notes, paid_on, session_id, paid_by
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            'paid', ?, ?, ?, ?
        )
    """)
    query.addBindValue(employee_id)
    query.addBindValue(month)
    query.addBindValue(basic_salary)
    query.addBindValue(allowances)
    query.addBindValue(deductions)
    query.addBindValue(advance_deduct)
    query.addBindValue(net_salary)
    query.addBindValue(payment_data.get("payment_method", ""))
    query.addBindValue(payment_data.get("bank_name", "") or None)
    query.addBindValue(payment_data.get("account_no", "") or None)
    query.addBindValue(payment_data.get("transaction_mode", "") or None)
    query.addBindValue(payment_data.get("wallet_provider", "") or None)
    query.addBindValue(payment_data.get("wallet_no", "") or None)
    query.addBindValue(payment_data.get("payment_reference", "") or None)
    query.addBindValue(notes or None)
    query.addBindValue(paid_on)
    query.addBindValue(session_id)
    query.addBindValue(paid_by)
    if query.exec():
        return True, query.lastInsertId()
    return False, query.lastError().text()


def apply_advance_recovery(advance_id, recovery_amount):
    """
    Add recovery_amount to salary_advance.recovered.
    Updates status to 'partial' or 'recovered' automatically.
    Returns True on success.
    """
    query = QSqlQuery()
    query.prepare("""
        UPDATE salary_advance
        SET
            recovered = COALESCE(recovered, 0) + ?,
            status = CASE
                WHEN COALESCE(recovered, 0) + ? >= amount THEN 'recovered'
                ELSE 'partial'
            END
        WHERE id = ?
    """)
    query.addBindValue(recovery_amount)
    query.addBindValue(recovery_amount)
    query.addBindValue(advance_id)
    return query.exec()


def save_payroll_entry(
    *,
    employee_id,
    month,
    basic_salary,
    allowances,
    deductions,
    advance_deduct,
    net_salary,
    payment_data,
    notes,
    paid_on,
    session_id,
    paid_by,
    pending_advances,
):
    def _work():
        ok, result = insert_payroll(
            employee_id,
            month,
            basic_salary,
            allowances,
            deductions,
            advance_deduct,
            net_salary,
            payment_data,
            notes,
            paid_on,
            session_id,
            paid_by,
        )
        if not ok:
            raise Exception(result)

        remaining_recovery = float(advance_deduct or 0.0)
        for advance in list(pending_advances or []):
            if remaining_recovery <= 0:
                break
            outstanding = float(advance["amount"] or 0.0) - float(advance["recovered"] or 0.0)
            this_recovery = min(remaining_recovery, outstanding)
            if this_recovery > 0:
                if not apply_advance_recovery(advance["id"], this_recovery):
                    raise Exception("Failed to update advance recovery record.")
                remaining_recovery -= this_recovery

        if float(advance_deduct or 0.0) > 0:
            if not update_employee_advance_balance(None, employee_id, -float(advance_deduct or 0.0)):
                raise Exception("Failed to update employee advance balance.")

        return result

    return run_in_transaction(
        _work,
        start_error_message="Could not start payroll transaction.",
        commit_error_message="Could not commit payroll transaction.",
    )
