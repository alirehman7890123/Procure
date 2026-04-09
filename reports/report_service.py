
from PySide6.QtSql import  QSqlQuery
from PySide6.QtCore import QDate



class ReportService:

    def _duration_where(self, column_expr, duration="today"):
        duration = (duration or "today").lower()
        if duration == "today":
            return f"DATE({column_expr}) = DATE('now')"
        if duration == "week":
            return f"DATE({column_expr}) >= DATE('now','-6 days')"
        if duration == "month":
            return f"DATE({column_expr}) >= DATE('now','-29 days')"
        if duration == "year":
            return f"DATE({column_expr}) >= DATE('now','-1 year')"
        if duration == "all":
            return "1=1"
        return f"DATE({column_expr}) = DATE('now')"

    def get_latest_session_cash_position(self):
        query = QSqlQuery()
        sql = """
            SELECT
                id,
                COALESCE(session_date, ''),
                COALESCE(status, 'closed'),
                COALESCE(opening_cash, 0),
                COALESCE(system_cash, 0),
                actual_cash,
                COALESCE(opened_at, ''),
                COALESCE(closed_at, '')
            FROM daily_session
            ORDER BY id DESC
            LIMIT 1
        """

        if not query.exec(sql):
            print("Latest session cash query failed:", query.lastError().text())
            return {
                "has_session": False,
                "cash_value": 0.0,
                "status": "none",
                "label": "No session",
                "session_date": "",
            }

        if query.next():
            status = str(query.value(2) or "closed").strip().lower()
            opening_cash = float(query.value(3) or 0.0)
            system_cash = float(query.value(4) or 0.0)
            actual_cash_raw = query.value(5)
            actual_cash = float(actual_cash_raw or 0.0) if actual_cash_raw not in (None, "") else None
            session_date = str(query.value(1) or "")

            if status == "open":
                cash_value = system_cash if system_cash else opening_cash
                label = "Open session system cash"
            else:
                cash_value = actual_cash if actual_cash is not None else (system_cash if system_cash else opening_cash)
                label = "Last closed session cash"

            return {
                "has_session": True,
                "cash_value": float(cash_value or 0.0),
                "status": status,
                "label": label,
                "session_date": session_date,
            }

        return {
            "has_session": False,
            "cash_value": 0.0,
            "status": "none",
            "label": "No session",
            "session_date": "",
        }

    def get_current_inventory_snapshot(self):
        query = QSqlQuery()
        sql = """
            SELECT
                COALESCE(SUM(CASE
                    WHEN COALESCE(b.quantity_remaining, 0) > 0 AND b.unit_cost IS NOT NULL
                    THEN COALESCE(b.quantity_remaining, 0) * COALESCE(b.unit_cost, 0)
                    ELSE 0 END), 0) AS known_inventory_value,
                COALESCE(SUM(CASE
                    WHEN COALESCE(b.quantity_remaining, 0) > 0 AND b.unit_cost IS NULL
                    THEN COALESCE(b.quantity_remaining, 0)
                    ELSE 0 END), 0) AS unknown_cost_units,
                COALESCE(SUM(CASE
                    WHEN COALESCE(b.quantity_remaining, 0) > 0 AND b.unit_cost IS NULL
                    THEN 1 ELSE 0 END), 0) AS unknown_cost_batches,
                COALESCE(SUM(CASE
                    WHEN COALESCE(b.quantity_remaining, 0) > 0
                    THEN COALESCE(b.quantity_remaining, 0)
                    ELSE 0 END), 0) AS total_units
            FROM batch b
        """

        if not query.exec(sql):
            print("Current inventory snapshot query failed:", query.lastError().text())
            return {
                "known_inventory_value": 0.0,
                "unknown_cost_units": 0.0,
                "unknown_cost_batches": 0,
                "total_units": 0.0,
            }

        if query.next():
            return {
                "known_inventory_value": float(query.value(0) or 0.0),
                "unknown_cost_units": float(query.value(1) or 0.0),
                "unknown_cost_batches": int(query.value(2) or 0),
                "total_units": float(query.value(3) or 0.0),
            }

        return {
            "known_inventory_value": 0.0,
            "unknown_cost_units": 0.0,
            "unknown_cost_batches": 0,
            "total_units": 0.0,
        }

    def get_cash_flow_summary(self, duration="today"):
        duration = (duration or "today").lower()
        if duration == "today":
            date_filter = "DATE(creation_date) = DATE('now')"
        elif duration == "week":
            date_filter = "DATE(creation_date) >= DATE('now','-6 days')"
        elif duration == "month":
            date_filter = "DATE(creation_date) >= DATE('now','-29 days')"
        elif duration == "year":
            date_filter = "DATE(creation_date) >= DATE('now','-1 year')"
        else:
            date_filter = "1=1"

        def fetch_transaction_summary(table_name):
            query = QSqlQuery()
            sql = f"""
                SELECT
                    COALESCE(SUM(received), 0),
                    COALESCE(SUM(paid), 0),
                    COUNT(*)
                FROM {table_name}
                WHERE {date_filter}
                  AND payment_method = 'Cash'
            """
            if not query.exec(sql):
                print(f"Cash flow query failed for {table_name}:", query.lastError().text())
                return 0.0, 0.0, 0
            if query.next():
                return (
                    float(query.value(0) or 0.0),
                    float(query.value(1) or 0.0),
                    int(query.value(2) or 0),
                )
            return 0.0, 0.0, 0

        customer_received, customer_paid, customer_rows = fetch_transaction_summary("customer_transaction")
        supplier_received, supplier_paid, supplier_rows = fetch_transaction_summary("supplier_transaction")

        expense_query = QSqlQuery()
        expense_sql = f"""
            SELECT
                COALESCE(SUM(amount), 0),
                COUNT(*)
            FROM expense
            WHERE {date_filter}
              AND payment_method = 'Cash'
        """
        cash_expenses = 0.0
        expense_rows = 0
        if expense_query.exec(expense_sql) and expense_query.next():
            cash_expenses = float(expense_query.value(0) or 0.0)
            expense_rows = int(expense_query.value(1) or 0)
        else:
            print("Cash flow expense query failed:", expense_query.lastError().text())

        total_inflows = customer_received + supplier_received
        total_outflows = customer_paid + supplier_paid + cash_expenses

        return {
            "customer_received": customer_received,
            "customer_paid": customer_paid,
            "supplier_received": supplier_received,
            "supplier_paid": supplier_paid,
            "cash_expenses": cash_expenses,
            "total_inflows": total_inflows,
            "total_outflows": total_outflows,
            "net_cash_movement": total_inflows - total_outflows,
            "customer_rows": customer_rows,
            "supplier_rows": supplier_rows,
            "expense_rows": expense_rows,
        }

    def get_credit_limit_utilization_rows(self):
        query = QSqlQuery()
        sql = """
            SELECT
                c.id,
                COALESCE(c.name, 'Walk-in Customer') AS customer_name,
                COALESCE(c.credit_limit, 0),
                COALESCE(c.receiveable, 0),
                COALESCE(c.payable, 0)
            FROM customer c
            WHERE COALESCE(c.credit_limit, 0) > 0
               OR COALESCE(c.receiveable, 0) > 0
            ORDER BY
                CASE
                    WHEN COALESCE(c.credit_limit, 0) > 0
                    THEN COALESCE(c.receiveable, 0) / COALESCE(NULLIF(c.credit_limit, 0), 1)
                    ELSE 0
                END DESC,
                COALESCE(c.receiveable, 0) DESC,
                c.name ASC
        """
        if not query.exec(sql):
            print("Credit limit utilization query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            customer_id = int(query.value(0) or 0)
            customer_name = str(query.value(1) or "")
            credit_limit = float(query.value(2) or 0.0)
            receivable = float(query.value(3) or 0.0)
            payable = float(query.value(4) or 0.0)
            available_credit = credit_limit - receivable
            utilization_pct = (receivable / credit_limit * 100.0) if credit_limit > 0 else 0.0

            if credit_limit <= 0:
                status = "No Limit"
            elif utilization_pct > 100:
                status = "Over Limit"
            elif utilization_pct >= 80:
                status = "Near Limit"
            else:
                status = "Available"

            rows.append({
                "customer_id": customer_id,
                "customer_name": customer_name,
                "credit_limit": credit_limit,
                "receivable": receivable,
                "payable": payable,
                "available_credit": available_credit,
                "utilization_pct": utilization_pct,
                "status": status,
            })

        return rows

    def get_sales_summary_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("s.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                s.id,
                DATE(s.creation_date) AS sales_date,
                COALESCE(c.name, 'Walk-in Customer') AS customer_name,
                COALESCE(a.username, '') AS salesman_name,
                COALESCE(s.total, 0),
                COALESCE(s.received, 0),
                COALESCE(s.remaining, 0),
                COALESCE(s.payable, 0),
                COALESCE(s.receiveable, 0)
            FROM sales s
            LEFT JOIN customer c ON c.id = s.customer
            LEFT JOIN auth a ON a.id = s.salesman
            WHERE {where_clause}
            ORDER BY datetime(s.creation_date) DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Sales summary rows query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "sales_id": int(query.value(0) or 0),
                "sales_date": str(query.value(1) or ""),
                "customer_name": str(query.value(2) or ""),
                "salesman_name": str(query.value(3) or ""),
                "total": float(query.value(4) or 0.0),
                "received": float(query.value(5) or 0.0),
                "remaining": float(query.value(6) or 0.0),
                "payable": float(query.value(7) or 0.0),
                "receivable": float(query.value(8) or 0.0),
            })
        return rows

    def get_sales_by_product_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("si.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                COALESCE(p.id, 0),
                COALESCE(p.display_name, 'Unknown Product') AS product_name,
                COALESCE(SUM(si.qty_sold), 0) AS qty_sold,
                COALESCE(SUM(si.effective_line_total), 0) AS sales_value,
                COALESCE(AVG(si.unit_price), 0) AS avg_unit_price
            FROM salesitem si
            LEFT JOIN product p ON p.id = si.product_id
            WHERE {where_clause}
            GROUP BY p.id, p.display_name
            HAVING COALESCE(SUM(si.qty_sold), 0) > 0
            ORDER BY sales_value DESC, qty_sold DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Sales by product query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "product_id": int(query.value(0) or 0),
                "product_name": str(query.value(1) or ""),
                "qty_sold": float(query.value(2) or 0.0),
                "sales_value": float(query.value(3) or 0.0),
                "avg_unit_price": float(query.value(4) or 0.0),
            })
        return rows

    def get_sales_by_customer_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("s.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                COALESCE(c.id, 0),
                COALESCE(c.name, 'Walk-in Customer') AS customer_name,
                COUNT(*) AS invoice_count,
                COALESCE(SUM(s.total), 0) AS total_sales,
                COALESCE(SUM(s.received), 0) AS total_received,
                COALESCE(SUM(s.remaining), 0) AS total_remaining
            FROM sales s
            LEFT JOIN customer c ON c.id = s.customer
            WHERE {where_clause}
            GROUP BY c.id, c.name
            HAVING COALESCE(SUM(s.total), 0) > 0
            ORDER BY total_sales DESC, invoice_count DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Sales by customer query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "customer_id": int(query.value(0) or 0),
                "customer_name": str(query.value(1) or ""),
                "invoice_count": int(query.value(2) or 0),
                "total_sales": float(query.value(3) or 0.0),
                "total_received": float(query.value(4) or 0.0),
                "total_remaining": float(query.value(5) or 0.0),
            })
        return rows

    def get_sales_by_rep_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("s.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                COALESCE(a.id, 0),
                COALESCE(a.username, 'Unknown User') AS rep_name,
                COUNT(*) AS invoice_count,
                COALESCE(SUM(s.total), 0) AS total_sales,
                COALESCE(SUM(s.received), 0) AS total_received
            FROM sales s
            LEFT JOIN auth a ON a.id = s.salesman
            WHERE {where_clause}
            GROUP BY a.id, a.username
            HAVING COALESCE(SUM(s.total), 0) > 0
            ORDER BY total_sales DESC, invoice_count DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Sales by rep query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "rep_id": int(query.value(0) or 0),
                "rep_name": str(query.value(1) or ""),
                "invoice_count": int(query.value(2) or 0),
                "total_sales": float(query.value(3) or 0.0),
                "total_received": float(query.value(4) or 0.0),
            })
        return rows

    def get_sales_return_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("sr.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                sr.id,
                DATE(sr.creation_date) AS return_date,
                COALESCE(c.name, 'Walk-in Customer') AS customer_name,
                COALESCE(sr.salesorder, 0) AS sales_id,
                COALESCE(sr.total, 0) AS total,
                COALESCE(sr.paid, 0) AS paid,
                COALESCE(sr.remaining, 0) AS remaining
            FROM salesreturn sr
            LEFT JOIN customer c ON c.id = sr.customer
            WHERE {where_clause}
            ORDER BY datetime(sr.creation_date) DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Sales return query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "return_id": int(query.value(0) or 0),
                "return_date": str(query.value(1) or ""),
                "customer_name": str(query.value(2) or ""),
                "sales_id": int(query.value(3) or 0),
                "total": float(query.value(4) or 0.0),
                "paid": float(query.value(5) or 0.0),
                "remaining": float(query.value(6) or 0.0),
            })
        return rows

    def get_receipt_list_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("ct.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                ct.id,
                DATE(ct.creation_date) AS receipt_date,
                COALESCE(c.name, 'Walk-in Customer') AS customer_name,
                COALESCE(ct.transaction_type, '') AS transaction_type,
                COALESCE(ct.ref, 0) AS ref_id,
                COALESCE(ct.received, 0) AS amount_received,
                COALESCE(ct.payment_method, '') AS payment_method,
                COALESCE(ct.payment_reference, '') AS payment_reference
            FROM customer_transaction ct
            LEFT JOIN customer c ON c.id = ct.customer
            WHERE {where_clause}
              AND COALESCE(ct.received, 0) > 0
            ORDER BY datetime(ct.creation_date) DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Receipt list query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "receipt_id": int(query.value(0) or 0),
                "receipt_date": str(query.value(1) or ""),
                "customer_name": str(query.value(2) or ""),
                "transaction_type": str(query.value(3) or ""),
                "ref_id": int(query.value(4) or 0),
                "amount_received": float(query.value(5) or 0.0),
                "payment_method": str(query.value(6) or ""),
                "payment_reference": str(query.value(7) or ""),
            })
        return rows

    def get_profit_by_sale_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("si.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            WITH sold_batch_rollup AS (
                SELECT
                    sb.sale_item_id,
                    SUM(CASE WHEN sb.unit_cost IS NOT NULL THEN COALESCE(sb.line_cost, 0) ELSE 0 END) AS known_cogs,
                    SUM(CASE WHEN sb.unit_cost IS NULL THEN 1 ELSE 0 END) AS unknown_cost_rows,
                    COUNT(*) AS batch_rows
                FROM sold_batch sb
                GROUP BY sb.sale_item_id
            ),
            sale_rollup AS (
                SELECT
                    s.id AS sales_id,
                    DATE(s.creation_date) AS sales_date,
                    COALESCE(c.name, 'Walk-in Customer') AS customer_name,
                    COALESCE(a.username, '') AS salesman_name,
                    SUM(CASE
                        WHEN COALESCE(sbr.unknown_cost_rows, 0) = 0
                         AND COALESCE(sbr.batch_rows, 0) > 0
                        THEN COALESCE(si.effective_line_total, 0)
                        ELSE 0 END) AS known_revenue,
                    SUM(CASE
                        WHEN COALESCE(sbr.unknown_cost_rows, 0) = 0
                         AND COALESCE(sbr.batch_rows, 0) > 0
                        THEN COALESCE(sbr.known_cogs, 0)
                        ELSE 0 END) AS known_cogs,
                    SUM(CASE
                        WHEN COALESCE(sbr.unknown_cost_rows, 0) > 0
                          OR COALESCE(sbr.batch_rows, 0) = 0
                        THEN COALESCE(si.effective_line_total, 0)
                        ELSE 0 END) AS unknown_revenue
                FROM salesitem si
                JOIN sales s ON s.id = si.sales_id
                LEFT JOIN sold_batch_rollup sbr ON sbr.sale_item_id = si.id
                LEFT JOIN customer c ON c.id = s.customer
                LEFT JOIN auth a ON a.id = s.salesman
                WHERE {where_clause}
                GROUP BY s.id, DATE(s.creation_date), c.name, a.username
            )
            SELECT
                sales_id,
                sales_date,
                customer_name,
                salesman_name,
                COALESCE(known_revenue, 0),
                COALESCE(known_cogs, 0),
                COALESCE(known_revenue, 0) - COALESCE(known_cogs, 0) AS known_profit,
                COALESCE(unknown_revenue, 0)
            FROM sale_rollup
            WHERE (COALESCE(known_revenue, 0) + COALESCE(unknown_revenue, 0)) > 0
            ORDER BY known_profit ASC, sales_id DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Profit by sale query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            known_revenue = float(query.value(4) or 0.0)
            known_cogs = float(query.value(5) or 0.0)
            known_profit = float(query.value(6) or 0.0)
            unknown_revenue = float(query.value(7) or 0.0)
            total_revenue = known_revenue + unknown_revenue
            rows.append({
                "sales_id": int(query.value(0) or 0),
                "sales_date": str(query.value(1) or ""),
                "customer_name": str(query.value(2) or ""),
                "salesman_name": str(query.value(3) or ""),
                "known_revenue": known_revenue,
                "known_cogs": known_cogs,
                "known_profit": known_profit,
                "unknown_revenue": unknown_revenue,
                "coverage_pct": (known_revenue / total_revenue * 100.0) if total_revenue > 0 else 0.0,
            })
        return rows

    def get_daily_sales_register_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("s.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                DATE(s.creation_date) AS sales_date,
                COUNT(*) AS invoice_count,
                COALESCE(SUM(s.total), 0) AS total_sales,
                COALESCE(SUM(s.received), 0) AS total_received,
                COALESCE(SUM(s.remaining), 0) AS total_remaining
            FROM sales s
            WHERE {where_clause}
            GROUP BY DATE(s.creation_date)
            HAVING COUNT(*) > 0
            ORDER BY sales_date DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Daily sales register query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "sales_date": str(query.value(0) or ""),
                "invoice_count": int(query.value(1) or 0),
                "total_sales": float(query.value(2) or 0.0),
                "total_received": float(query.value(3) or 0.0),
                "total_remaining": float(query.value(4) or 0.0),
            })
        return rows

    def get_purchase_summary_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("p.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                p.id,
                DATE(p.creation_date) AS purchase_date,
                COALESCE(s.name, '') AS supplier_name,
                COALESCE(r.name, '') AS rep_name,
                COALESCE(p.sellerinvoice, '') AS seller_invoice,
                COALESCE(p.total, 0),
                COALESCE(p.paid, 0),
                COALESCE(p.remaining, 0)
            FROM purchase p
            LEFT JOIN supplier s ON s.id = p.supplier
            LEFT JOIN rep r ON r.id = p.rep
            WHERE {where_clause}
            ORDER BY datetime(p.creation_date) DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Purchase summary rows query failed:", query.lastError().text())
            return []
        rows = []
        while query.next():
            rows.append({
                "purchase_id": int(query.value(0) or 0),
                "purchase_date": str(query.value(1) or ""),
                "supplier_name": str(query.value(2) or ""),
                "rep_name": str(query.value(3) or ""),
                "seller_invoice": str(query.value(4) or ""),
                "total": float(query.value(5) or 0.0),
                "paid": float(query.value(6) or 0.0),
                "remaining": float(query.value(7) or 0.0),
            })
        return rows

    def get_purchase_by_supplier_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("p.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                COALESCE(s.id, 0),
                COALESCE(s.name, 'Unknown Supplier'),
                COUNT(*) AS invoice_count,
                COALESCE(SUM(p.total), 0) AS total_purchase,
                COALESCE(SUM(p.paid), 0) AS total_paid,
                COALESCE(SUM(p.remaining), 0) AS total_remaining
            FROM purchase p
            LEFT JOIN supplier s ON s.id = p.supplier
            WHERE {where_clause}
            GROUP BY s.id, s.name
            HAVING COALESCE(SUM(p.total), 0) > 0
            ORDER BY total_purchase DESC, invoice_count DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Purchase by supplier query failed:", query.lastError().text())
            return []
        rows = []
        while query.next():
            rows.append({
                "supplier_id": int(query.value(0) or 0),
                "supplier_name": str(query.value(1) or ""),
                "invoice_count": int(query.value(2) or 0),
                "total_purchase": float(query.value(3) or 0.0),
                "total_paid": float(query.value(4) or 0.0),
                "total_remaining": float(query.value(5) or 0.0),
            })
        return rows

    def get_purchase_by_product_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("pi.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                COALESCE(pr.id, 0),
                COALESCE(pr.display_name, 'Unknown Product'),
                COALESCE(SUM(pi.qty + pi.bonus), 0) AS qty_received,
                COALESCE(SUM(pi.total), 0) AS purchase_value,
                COALESCE(AVG(pi.rate), 0) AS avg_rate
            FROM purchaseitem pi
            LEFT JOIN product pr ON pr.id = pi.product
            WHERE {where_clause}
            GROUP BY pr.id, pr.display_name
            HAVING COALESCE(SUM(pi.total), 0) > 0
            ORDER BY purchase_value DESC, qty_received DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Purchase by product query failed:", query.lastError().text())
            return []
        rows = []
        while query.next():
            rows.append({
                "product_id": int(query.value(0) or 0),
                "product_name": str(query.value(1) or ""),
                "qty_received": float(query.value(2) or 0.0),
                "purchase_value": float(query.value(3) or 0.0),
                "avg_rate": float(query.value(4) or 0.0),
            })
        return rows

    def get_po_status_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("po.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                po.id,
                COALESCE(po.po_number, ''),
                COALESCE(po.po_date, ''),
                COALESCE(s.name, '') AS supplier_name,
                COALESCE(po.status, 'draft'),
                COALESCE(po.total_value, 0),
                COALESCE((SELECT SUM(qty_ordered) FROM purchase_order_line WHERE po_id = po.id), 0) AS ordered_qty,
                COALESCE((
                    SELECT SUM(grl.qty_received)
                    FROM goods_receipt_line grl
                    JOIN purchase_order_line pol ON pol.id = grl.po_line_id
                    WHERE pol.po_id = po.id
                ), 0) AS received_qty,
                COALESCE(SUM(gr.total_value), 0) AS grn_value,
                COUNT(gr.id) AS grn_count
            FROM purchase_order po
            LEFT JOIN supplier s ON s.id = po.supplier
            LEFT JOIN goods_receipt gr ON gr.po_id = po.id
            WHERE {where_clause}
            GROUP BY po.id, po.po_number, po.po_date, s.name, po.status, po.total_value
            ORDER BY datetime(po.creation_date) DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("PO status query failed:", query.lastError().text())
            return []
        rows = []
        while query.next():
            rows.append({
                "po_id": int(query.value(0) or 0),
                "po_number": str(query.value(1) or ""),
                "po_date": str(query.value(2) or ""),
                "supplier_name": str(query.value(3) or ""),
                "status": str(query.value(4) or ""),
                "total_value": float(query.value(5) or 0.0),
                "ordered_qty": float(query.value(6) or 0.0),
                "received_qty": float(query.value(7) or 0.0),
                "remaining_qty": max(float(query.value(6) or 0.0) - float(query.value(7) or 0.0), 0.0),
                "grn_value": float(query.value(8) or 0.0),
                "grn_count": int(query.value(9) or 0),
            })
        return rows

    def get_grn_status_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("gr.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                gr.id,
                COALESCE(gr.grn_number, ''),
                COALESCE(gr.grn_date, ''),
                COALESCE(po.po_number, ''),
                COALESCE(s.name, '') AS supplier_name,
                COALESCE(gr.status, 'draft'),
                COALESCE(gr.total_value, 0),
                COUNT(grl.id) AS line_count
            FROM goods_receipt gr
            LEFT JOIN purchase_order po ON po.id = gr.po_id
            LEFT JOIN supplier s ON s.id = po.supplier
            LEFT JOIN goods_receipt_line grl ON grl.grn_id = gr.id
            WHERE {where_clause}
            GROUP BY gr.id, gr.grn_number, gr.grn_date, po.po_number, s.name, gr.status, gr.total_value
            ORDER BY datetime(gr.creation_date) DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("GRN status query failed:", query.lastError().text())
            return []
        rows = []
        while query.next():
            rows.append({
                "grn_id": int(query.value(0) or 0),
                "grn_number": str(query.value(1) or ""),
                "grn_date": str(query.value(2) or ""),
                "po_number": str(query.value(3) or ""),
                "supplier_name": str(query.value(4) or ""),
                "status": str(query.value(5) or ""),
                "total_value": float(query.value(6) or 0.0),
                "line_count": int(query.value(7) or 0),
            })
        return rows

    def get_partial_po_receipt_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("po.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            WITH po_totals AS (
                SELECT
                    po.id,
                    COALESCE(po.po_number, '') AS po_number,
                    COALESCE(po.po_date, '') AS po_date,
                    COALESCE(s.name, '') AS supplier_name,
                    COALESCE(po.status, 'draft') AS status,
                    COALESCE(po.total_value, 0) AS total_value,
                    COALESCE((SELECT SUM(qty_ordered) FROM purchase_order_line WHERE po_id = po.id), 0) AS ordered_qty,
                    COALESCE((
                        SELECT SUM(grl.qty_received)
                        FROM goods_receipt_line grl
                        JOIN purchase_order_line pol ON pol.id = grl.po_line_id
                        WHERE pol.po_id = po.id
                    ), 0) AS received_qty,
                    COALESCE((SELECT COUNT(*) FROM goods_receipt WHERE po_id = po.id), 0) AS grn_count,
                    CAST(julianday('now') - julianday(COALESCE(po.po_date, date('now'))) AS INTEGER) AS days_open
                FROM purchase_order po
                LEFT JOIN supplier s ON s.id = po.supplier
                WHERE {where_clause}
            )
            SELECT
                id,
                po_number,
                po_date,
                supplier_name,
                status,
                total_value,
                ordered_qty,
                received_qty,
                grn_count,
                days_open
            FROM po_totals
            WHERE ordered_qty > 0
              AND received_qty > 0
              AND received_qty < ordered_qty
            ORDER BY days_open DESC, po_date ASC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Partial PO receipt query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            ordered_qty = float(query.value(6) or 0.0)
            received_qty = float(query.value(7) or 0.0)
            remaining_qty = max(ordered_qty - received_qty, 0.0)
            completion_pct = (received_qty / ordered_qty * 100.0) if ordered_qty > 0 else 0.0
            rows.append({
                "po_id": int(query.value(0) or 0),
                "po_number": str(query.value(1) or ""),
                "po_date": str(query.value(2) or ""),
                "supplier_name": str(query.value(3) or ""),
                "status": str(query.value(4) or ""),
                "total_value": float(query.value(5) or 0.0),
                "ordered_qty": ordered_qty,
                "received_qty": received_qty,
                "remaining_qty": remaining_qty,
                "completion_pct": completion_pct,
                "grn_count": int(query.value(8) or 0),
                "days_open": int(query.value(9) or 0),
            })
        return rows

    def get_purchase_return_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("pr.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                pr.id,
                DATE(pr.creation_date) AS return_date,
                COALESCE(s.name, '') AS supplier_name,
                COALESCE(r.name, '') AS rep_name,
                COALESCE(pr.total, 0),
                COALESCE(pr.received, 0),
                COALESCE(pr.remaining, 0)
            FROM purchase_return pr
            LEFT JOIN supplier s ON s.id = pr.supplier
            LEFT JOIN rep r ON r.id = pr.rep
            WHERE {where_clause}
            ORDER BY datetime(pr.creation_date) DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Purchase return query failed:", query.lastError().text())
            return []
        rows = []
        while query.next():
            rows.append({
                "return_id": int(query.value(0) or 0),
                "return_date": str(query.value(1) or ""),
                "supplier_name": str(query.value(2) or ""),
                "rep_name": str(query.value(3) or ""),
                "total": float(query.value(4) or 0.0),
                "received": float(query.value(5) or 0.0),
                "remaining": float(query.value(6) or 0.0),
            })
        return rows

    def get_supplier_payment_summary_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("st.creation_date", duration)
        latest_where_clause = self._duration_where("st2.creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                COALESCE(s.id, 0),
                COALESCE(s.name, 'Unknown Supplier'),
                COUNT(*) AS txn_count,
                COALESCE(SUM(st.paid), 0) AS total_paid,
                COALESCE(SUM(st.received), 0) AS total_received,
                COALESCE((
                    SELECT st2.payable_after
                    FROM supplier_transaction st2
                    WHERE st2.supplier = s.id
                      AND {latest_where_clause}
                    ORDER BY st2.creation_date DESC, st2.id DESC
                    LIMIT 1
                ), 0) AS payable_after,
                COALESCE((
                    SELECT st2.receiveable_after
                    FROM supplier_transaction st2
                    WHERE st2.supplier = s.id
                      AND {latest_where_clause}
                    ORDER BY st2.creation_date DESC, st2.id DESC
                    LIMIT 1
                ), 0) AS receivable_after
            FROM supplier_transaction st
            LEFT JOIN supplier s ON s.id = st.supplier
            WHERE {where_clause}
            GROUP BY s.id, s.name
            HAVING txn_count > 0
            ORDER BY total_paid DESC, txn_count DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Supplier payment summary query failed:", query.lastError().text())
            return []
        rows = []
        while query.next():
            rows.append({
                "supplier_id": int(query.value(0) or 0),
                "supplier_name": str(query.value(1) or ""),
                "txn_count": int(query.value(2) or 0),
                "total_paid": float(query.value(3) or 0.0),
                "total_received": float(query.value(4) or 0.0),
                "payable_after": float(query.value(5) or 0.0),
                "receivable_after": float(query.value(6) or 0.0),
            })
        return rows

    def get_purchase_vs_sales_comparison_rows(self, duration="today", limit=500):
        duration = (duration or "today").lower()
        if duration == "today":
            purchase_key = "DATE(creation_date)"
            sales_key = "DATE(creation_date)"
        elif duration == "week":
            purchase_key = "DATE(creation_date)"
            sales_key = "DATE(creation_date)"
        elif duration == "month":
            purchase_key = "DATE(creation_date)"
            sales_key = "DATE(creation_date)"
        elif duration == "year":
            purchase_key = "strftime('%Y-%m', DATE(creation_date))"
            sales_key = "strftime('%Y-%m', DATE(creation_date))"
        else:
            purchase_key = "strftime('%Y-%m', DATE(creation_date))"
            sales_key = "strftime('%Y-%m', DATE(creation_date))"

        purchase_where = self._duration_where("creation_date", duration)
        sales_where = self._duration_where("creation_date", duration)
        query = QSqlQuery()
        sql = f"""
            WITH purchase_rollup AS (
                SELECT {purchase_key} AS period_key, COALESCE(SUM(total), 0) AS purchase_total
                FROM purchase
                WHERE {purchase_where}
                GROUP BY {purchase_key}
            ),
            sales_rollup AS (
                SELECT {sales_key} AS period_key, COALESCE(SUM(total), 0) AS sales_total
                FROM sales
                WHERE {sales_where}
                GROUP BY {sales_key}
            ),
            periods AS (
                SELECT period_key FROM purchase_rollup
                UNION
                SELECT period_key FROM sales_rollup
            )
            SELECT
                p.period_key,
                COALESCE(pr.purchase_total, 0),
                COALESCE(sr.sales_total, 0)
            FROM periods p
            LEFT JOIN purchase_rollup pr ON pr.period_key = p.period_key
            LEFT JOIN sales_rollup sr ON sr.period_key = p.period_key
            ORDER BY p.period_key DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Purchase vs sales comparison query failed:", query.lastError().text())
            return []
        rows = []
        while query.next():
            purchase_total = float(query.value(1) or 0.0)
            sales_total = float(query.value(2) or 0.0)
            rows.append({
                "period": str(query.value(0) or ""),
                "purchase_total": purchase_total,
                "sales_total": sales_total,
                "variance": sales_total - purchase_total,
            })
        return rows

    def get_stock_valuation_rows(self, limit=1000):
        query = QSqlQuery()
        sql = f"""
            SELECT
                COALESCE(p.id, 0),
                COALESCE(p.display_name, 'Unknown Product') AS product_name,
                COALESCE(SUM(CASE WHEN COALESCE(b.quantity_remaining, 0) > 0 THEN COALESCE(b.quantity_remaining, 0) ELSE 0 END), 0) AS stock_qty,
                COALESCE(SUM(CASE WHEN COALESCE(b.quantity_remaining, 0) > 0 AND b.unit_cost IS NOT NULL
                    THEN COALESCE(b.quantity_remaining, 0) * COALESCE(b.unit_cost, 0) ELSE 0 END), 0) AS known_stock_value,
                COALESCE(SUM(CASE WHEN COALESCE(b.quantity_remaining, 0) > 0 AND b.unit_cost IS NULL THEN COALESCE(b.quantity_remaining, 0) ELSE 0 END), 0) AS unknown_cost_units
            FROM product p
            LEFT JOIN batch b ON b.product_id = p.id
            WHERE p.status = 'used'
            GROUP BY p.id, p.display_name
            HAVING stock_qty > 0
            ORDER BY known_stock_value DESC, stock_qty DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Stock valuation query failed:", query.lastError().text())
            return []
        rows = []
        while query.next():
            rows.append({
                "product_id": int(query.value(0) or 0),
                "product_name": str(query.value(1) or ""),
                "stock_qty": float(query.value(2) or 0.0),
                "known_stock_value": float(query.value(3) or 0.0),
                "unknown_cost_units": float(query.value(4) or 0.0),
            })
        return rows

    def get_expired_stock_rows(self, limit=2000):
        query = QSqlQuery()
        sql = f"""
            SELECT
                b.id,
                COALESCE(p.id, 0),
                COALESCE(p.display_name, 'Unknown Product') AS product_name,
                COALESCE(b.batch_no, '') AS batch_no,
                COALESCE(b.expiry_date, '') AS expiry_date,
                COALESCE(b.quantity_remaining, 0) AS qty_remaining,
                COALESCE(b.unit_cost, 0) AS unit_cost,
                COALESCE(b.quantity_remaining, 0) * COALESCE(b.unit_cost, 0) AS stock_value,
                COALESCE(b.source, '') AS source
            FROM batch b
            LEFT JOIN product p ON p.id = b.product_id
            WHERE COALESCE(b.quantity_remaining, 0) > 0
              AND (
                    CASE
                        WHEN b.expiry_date LIKE '____-__-__' THEN date(b.expiry_date)
                        WHEN b.expiry_date LIKE '__-__-____'
                            THEN date(substr(b.expiry_date, 7, 4) || '-' || substr(b.expiry_date, 4, 2) || '-' || substr(b.expiry_date, 1, 2))
                        ELSE NULL
                    END
                  ) < date('now')
            ORDER BY date(
                CASE
                    WHEN b.expiry_date LIKE '____-__-__' THEN b.expiry_date
                    WHEN b.expiry_date LIKE '__-__-____'
                        THEN substr(b.expiry_date, 7, 4) || '-' || substr(b.expiry_date, 4, 2) || '-' || substr(b.expiry_date, 1, 2)
                    ELSE NULL
                END
            ) ASC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Expired stock query failed:", query.lastError().text())
            return []
        rows = []
        while query.next():
            rows.append({
                "batch_id": int(query.value(0) or 0),
                "product_id": int(query.value(1) or 0),
                "product_name": str(query.value(2) or ""),
                "batch_no": str(query.value(3) or ""),
                "expiry_date": str(query.value(4) or ""),
                "qty_remaining": float(query.value(5) or 0.0),
                "unit_cost": float(query.value(6) or 0.0),
                "stock_value": float(query.value(7) or 0.0),
                "source": str(query.value(8) or ""),
            })
        return rows

    def get_batch_traceability_rows(self, limit=2000):
        query = QSqlQuery()
        sql = f"""
            SELECT
                b.id,
                COALESCE(p.display_name, 'Unknown Product') AS product_name,
                COALESCE(b.batch_no, '') AS batch_no,
                COALESCE(b.expiry_date, '') AS expiry_date,
                COALESCE(b.total_received, 0) AS total_received,
                COALESCE(b.quantity_remaining, 0) AS quantity_remaining,
                COALESCE(b.unit_cost, 0) AS unit_cost,
                COALESCE(b.source, '') AS source,
                COALESCE(b.received_at, '') AS received_at
            FROM batch b
            LEFT JOIN product p ON p.id = b.product_id
            ORDER BY datetime(b.received_at) DESC, b.id DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Batch traceability query failed:", query.lastError().text())
            return []
        rows = []
        while query.next():
            rows.append({
                "batch_id": int(query.value(0) or 0),
                "product_name": str(query.value(1) or ""),
                "batch_no": str(query.value(2) or ""),
                "expiry_date": str(query.value(3) or ""),
                "total_received": float(query.value(4) or 0.0),
                "quantity_remaining": float(query.value(5) or 0.0),
                "unit_cost": float(query.value(6) or 0.0),
                "source": str(query.value(7) or ""),
                "received_at": str(query.value(8) or ""),
            })
        return rows

    def get_inventory_adjustment_rows(self, duration="today", limit=2000):
        where_clause = self._duration_where("ia.created_at", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                ia.id,
                DATE(ia.created_at) AS adjustment_date,
                COALESCE(p.display_name, 'Unknown Product') AS product_name,
                COALESCE(b.batch_no, '') AS batch_no,
                COALESCE(ia.adjustment_type, '') AS adjustment_type,
                COALESCE(ia.qty, 0) AS qty,
                COALESCE(ia.old_qty, 0) AS old_qty,
                COALESCE(ia.new_qty, 0) AS new_qty,
                COALESCE(ia.reason, '') AS reason,
                COALESCE(a.username, '') AS adjusted_by
            FROM inventory_adjustment ia
            LEFT JOIN batch b ON b.id = ia.batch_id
            LEFT JOIN product p ON p.id = b.product_id
            LEFT JOIN auth a ON a.id = ia.adjusted_by
            WHERE {where_clause}
            ORDER BY datetime(ia.created_at) DESC, ia.id DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Inventory adjustment query failed:", query.lastError().text())
            return []
        rows = []
        while query.next():
            rows.append({
                "adjustment_id": int(query.value(0) or 0),
                "adjustment_date": str(query.value(1) or ""),
                "product_name": str(query.value(2) or ""),
                "batch_no": str(query.value(3) or ""),
                "adjustment_type": str(query.value(4) or ""),
                "qty": float(query.value(5) or 0.0),
                "old_qty": float(query.value(6) or 0.0),
                "new_qty": float(query.value(7) or 0.0),
                "reason": str(query.value(8) or ""),
                "adjusted_by": str(query.value(9) or ""),
            })
        return rows

    def get_price_change_rows(self, duration="today", limit=1000):
        where_clause = self._duration_where("pc.created_at", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                pc.id,
                DATE(pc.created_at) AS change_date,
                COALESCE(p.display_name, 'Unknown Product') AS product_name,
                COALESCE(pc.previous_price, 0) AS previous_price,
                COALESCE(pc.new_price, 0) AS new_price,
                COALESCE(pc.new_price, 0) - COALESCE(pc.previous_price, 0) AS variance,
                COALESCE(pc.source, '') AS source,
                COALESCE(pc.username, '') AS username
            FROM price_changes pc
            LEFT JOIN product p ON p.id = pc.product_id
            WHERE {where_clause}
            ORDER BY datetime(pc.created_at) DESC, pc.id DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Price change query failed:", query.lastError().text())
            return []
        rows = []
        while query.next():
            rows.append({
                "change_id": int(query.value(0) or 0),
                "change_date": str(query.value(1) or ""),
                "product_name": str(query.value(2) or ""),
                "previous_price": float(query.value(3) or 0.0),
                "new_price": float(query.value(4) or 0.0),
                "variance": float(query.value(5) or 0.0),
                "source": str(query.value(6) or ""),
                "username": str(query.value(7) or ""),
            })
        return rows

    def get_login_activity_rows(self, duration="today", limit=1000):
        where_clause = self._duration_where("timestamp", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                id,
                COALESCE(timestamp, '') AS timestamp,
                COALESCE(username, '') AS username,
                COALESCE(action, '') AS action,
                COALESCE(note, '') AS note,
                COALESCE(login_session_id, '') AS login_session_id,
                COALESCE(daily_session_id, 0) AS daily_session_id
            FROM activity_log
            WHERE {where_clause}
              AND category = 'login'
            ORDER BY datetime(timestamp) DESC, id DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Login activity query failed:", query.lastError().text())
            return []
        rows = []
        while query.next():
            rows.append({
                "log_id": int(query.value(0) or 0),
                "timestamp": str(query.value(1) or ""),
                "username": str(query.value(2) or ""),
                "action": str(query.value(3) or ""),
                "note": str(query.value(4) or ""),
                "login_session_id": str(query.value(5) or ""),
                "daily_session_id": int(query.value(6) or 0),
            })
        return rows

    def get_shift_closing_summary_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("closed_at", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                id,
                COALESCE(session_date, '') AS session_date,
                COALESCE(opening_cash, 0) AS opening_cash,
                COALESCE(system_cash, 0) AS system_cash,
                COALESCE(actual_cash, 0) AS actual_cash,
                COALESCE(withdrawal, 0) AS withdrawal,
                COALESCE(cash_difference, 0) AS cash_difference,
                COALESCE(opened_at, '') AS opened_at,
                COALESCE(closed_at, '') AS closed_at,
                COALESCE(status, '') AS status
            FROM daily_session
            WHERE status = 'closed'
              AND closed_at IS NOT NULL
              AND {where_clause}
            ORDER BY datetime(closed_at) DESC, id DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Shift closing summary query failed:", query.lastError().text())
            return []
        rows = []
        while query.next():
            rows.append({
                "session_id": int(query.value(0) or 0),
                "session_date": str(query.value(1) or ""),
                "opening_cash": float(query.value(2) or 0.0),
                "system_cash": float(query.value(3) or 0.0),
                "actual_cash": float(query.value(4) or 0.0),
                "withdrawal": float(query.value(5) or 0.0),
                "cash_difference": float(query.value(6) or 0.0),
                "opened_at": str(query.value(7) or ""),
                "closed_at": str(query.value(8) or ""),
                "status": str(query.value(9) or ""),
            })
        return rows

    def get_dead_nonmoving_stock(self, threshold_days=90, view_mode="all", limit=2000):
        """Return products with on-hand stock that are dead or non-moving."""

        try:
            threshold_days = int(threshold_days)
        except Exception:
            threshold_days = 90

        if threshold_days < 1:
            threshold_days = 1

        try:
            limit = int(limit)
        except Exception:
            limit = 2000

        if limit <= 0:
            limit = 2000

        view_mode = (view_mode or "all").lower()
        threshold_modifier = f"-{threshold_days} days"

        query = QSqlQuery()
        sql = """
            WITH stock_on_hand AS (
                SELECT
                    b.product_id,
                    COALESCE(p.display_name, 'Unknown Product') AS product_name,
                    SUM(COALESCE(b.quantity_remaining, 0)) AS stock_qty,
                    SUM(COALESCE(b.quantity_remaining, 0) * COALESCE(b.unit_cost, 0)) AS stock_value,
                    MIN(DATE(COALESCE(b.received_at, b.expiry_date, 'now'))) AS oldest_batch_date
                FROM batch b
                LEFT JOIN product p ON p.id = b.product_id
                WHERE COALESCE(b.quantity_remaining, 0) > 0
                GROUP BY b.product_id, p.display_name
            ),
            sales_rollup AS (
                SELECT
                    si.product_id,
                    MAX(DATE(si.creation_date)) AS last_sale_date,
                    SUM(COALESCE(si.qty_sold, 0)) AS total_sold
                FROM salesitem si
                GROUP BY si.product_id
            )
            SELECT
                soh.product_id,
                soh.product_name,
                soh.stock_qty,
                soh.stock_value,
                soh.oldest_batch_date,
                sr.last_sale_date,
                CAST(julianday('now') - julianday(sr.last_sale_date) AS INTEGER) AS days_since_last_sale,
                COALESCE(sr.total_sold, 0) AS total_sold,
                CASE
                    WHEN sr.last_sale_date IS NULL THEN 'DEAD'
                    WHEN DATE(sr.last_sale_date) < DATE('now', ?) THEN 'NON_MOVING'
                    ELSE 'ACTIVE'
                END AS stock_status
            FROM stock_on_hand soh
            LEFT JOIN sales_rollup sr ON sr.product_id = soh.product_id
            WHERE soh.stock_qty > 0
              AND (
                    sr.last_sale_date IS NULL
                 OR DATE(sr.last_sale_date) < DATE('now', ?)
              )
            ORDER BY soh.stock_value DESC, soh.stock_qty DESC
            LIMIT ?
        """

        query.prepare(sql)
        query.addBindValue(threshold_modifier)
        query.addBindValue(threshold_modifier)
        query.addBindValue(limit)

        if not query.exec():
            print("Dead/non-moving stock query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            row = {
                "product_id": int(query.value(0) or 0),
                "product_name": str(query.value(1) or ""),
                "stock_qty": float(query.value(2) or 0.0),
                "stock_value": float(query.value(3) or 0.0),
                "oldest_batch_date": str(query.value(4) or ""),
                "last_sale_date": str(query.value(5) or ""),
                "days_since_last_sale": int(query.value(6) or 0) if query.value(6) is not None else None,
                "total_sold": float(query.value(7) or 0.0),
                "stock_status": str(query.value(8) or "NON_MOVING"),
            }
            rows.append(row)

        if view_mode == "dead":
            return [r for r in rows if r.get("stock_status") == "DEAD"]
        if view_mode == "non_moving":
            return [r for r in rows if r.get("stock_status") == "NON_MOVING"]

        return rows

    def get_stock_movements(self, duration="month", product_id=None, movement_type="all", limit=1000):
        duration = (duration or "month").lower()
        movement_type = (movement_type or "all").upper()

        if duration == "today":
            date_filter = "DATE(movement_date) = DATE('now')"
        elif duration == "week":
            date_filter = "DATE(movement_date) >= DATE('now','-6 days')"
        elif duration == "month":
            date_filter = "DATE(movement_date) >= DATE('now','-29 days')"
        elif duration == "year":
            date_filter = "DATE(movement_date) >= DATE('now','-1 year')"
        else:
            date_filter = "1=1"

        sql = f"""
            WITH movements AS (
                SELECT
                    b.received_at AS movement_date,
                    CASE
                        WHEN COALESCE(b.source, '') = 'opening' THEN 'OPENING_STOCK'
                        ELSE 'PURCHASE_IN'
                    END AS movement_type,
                    p.id AS product_id,
                    p.display_name AS product_name,
                    COALESCE(b.batch_no, '') AS batch_no,
                    COALESCE(b.total_received, 0) AS qty_change,
                    CASE
                        WHEN b.purchaseitem_id IS NOT NULL THEN 'PI#' || CAST(b.purchaseitem_id AS TEXT)
                        ELSE 'BATCH#' || CAST(b.id AS TEXT)
                    END AS reference,
                    '' AS performed_by,
                    COALESCE(b.source, '') AS reason
                FROM batch b
                JOIN product p ON p.id = b.product_id
                WHERE COALESCE(b.total_received, 0) > 0

                UNION ALL

                SELECT
                    sb.created_at AS movement_date,
                    'SALE_OUT' AS movement_type,
                    p.id AS product_id,
                    p.display_name AS product_name,
                    COALESCE(b.batch_no, '') AS batch_no,
                    -COALESCE(sb.qty_taken, 0) AS qty_change,
                    'SALE#' || CAST(si.sales_id AS TEXT) AS reference,
                    COALESCE(a.username, '') AS performed_by,
                    '' AS reason
                FROM sold_batch sb
                JOIN batch b ON b.id = sb.batch_id
                JOIN salesitem si ON si.id = sb.sale_item_id
                JOIN product p ON p.id = si.product_id
                LEFT JOIN sales s ON s.id = si.sales_id
                LEFT JOIN auth a ON a.id = s.salesman
                WHERE COALESCE(sb.qty_taken, 0) > 0

                UNION ALL

                SELECT
                    sri.creation_date AS movement_date,
                    'SALES_RETURN_IN' AS movement_type,
                    p.id AS product_id,
                    p.display_name AS product_name,
                    '' AS batch_no,
                    COALESCE(sri.returned, 0) AS qty_change,
                    'SR#' || CAST(sri.salesreturn AS TEXT) AS reference,
                    '' AS performed_by,
                    'sales return' AS reason
                FROM salesreturn_item sri
                JOIN product p ON p.id = sri.product
                WHERE COALESCE(sri.returned, 0) > 0

                UNION ALL

                SELECT
                    pri.creation_date AS movement_date,
                    'PURCHASE_RETURN_OUT' AS movement_type,
                    p.id AS product_id,
                    p.display_name AS product_name,
                    COALESCE(pri.batch, '') AS batch_no,
                    -COALESCE(pri.returned, 0) AS qty_change,
                    'PR#' || CAST(pri.purchase_return AS TEXT) AS reference,
                    '' AS performed_by,
                    'purchase return' AS reason
                FROM purchase_return_item pri
                JOIN product p ON p.id = pri.product
                WHERE COALESCE(pri.returned, 0) > 0

                UNION ALL

                SELECT
                    ia.created_at AS movement_date,
                    CASE
                        WHEN ia.adjustment_type = 'addition' THEN 'ADJUSTMENT_IN'
                        ELSE 'ADJUSTMENT_OUT'
                    END AS movement_type,
                    p.id AS product_id,
                    p.display_name AS product_name,
                    COALESCE(b.batch_no, '') AS batch_no,
                    CASE
                        WHEN ia.adjustment_type = 'addition' THEN COALESCE(ia.qty, 0)
                        ELSE -COALESCE(ia.qty, 0)
                    END AS qty_change,
                    'ADJ#' || CAST(ia.id AS TEXT) AS reference,
                    COALESCE(a.username, '') AS performed_by,
                    COALESCE(ia.reason, '') AS reason
                FROM inventory_adjustment ia
                JOIN batch b ON b.id = ia.batch_id
                JOIN product p ON p.id = b.product_id
                LEFT JOIN auth a ON a.id = ia.adjusted_by
            )
            SELECT
                movement_date,
                movement_type,
                product_id,
                product_name,
                batch_no,
                qty_change,
                reference,
                performed_by,
                reason
            FROM movements
            WHERE {date_filter}
        """

        bind_values = []

        if product_id is not None:
            sql += " AND product_id = ?"
            bind_values.append(int(product_id))

        if movement_type != "ALL":
            sql += " AND movement_type = ?"
            bind_values.append(movement_type)

        sql += " ORDER BY datetime(movement_date) DESC LIMIT ?"
        bind_values.append(int(limit))

        rows = []
        query = QSqlQuery()
        query.prepare(sql)
        for value in bind_values:
            query.addBindValue(value)

        if not query.exec():
            print("Stock movement query failed:", query.lastError().text())
            return []

        while query.next():
            rows.append({
                "movement_date": str(query.value(0) or ""),
                "movement_type": str(query.value(1) or ""),
                "product_id": query.value(2),
                "product_name": str(query.value(3) or ""),
                "batch_no": str(query.value(4) or ""),
                "qty_change": int(query.value(5) or 0),
                "reference": str(query.value(6) or ""),
                "performed_by": str(query.value(7) or ""),
                "reason": str(query.value(8) or ""),
            })

        return rows


    def get_activity_log(self, duration="month", category=None, username=None, limit=500):
        duration = (duration or "month").lower()

        if duration == "today":
            date_filter = "DATE(timestamp) = DATE('now')"
        elif duration == "week":
            date_filter = "DATE(timestamp) >= DATE('now','-6 days')"
        elif duration == "month":
            date_filter = "DATE(timestamp) >= DATE('now','-29 days')"
        elif duration == "year":
            date_filter = "DATE(timestamp) >= DATE('now','-1 year')"
        else:
            date_filter = "1=1"

        sql = f"""
            SELECT
                timestamp,
                COALESCE(username, '') AS username,
                category,
                action,
                COALESCE(entity_type, '') AS entity_type,
                COALESCE(entity_id, '') AS entity_id,
                COALESCE(note, '') AS note,
                COALESCE(previous_value, '') AS previous_value,
                COALESCE(new_value, '') AS new_value
            FROM activity_log
            WHERE {date_filter}
        """

        bind_values = []

        if category:
            sql += " AND category = ?"
            bind_values.append(category)

        if username:
            sql += " AND username LIKE ?"
            bind_values.append(f"%{username}%")

        sql += " ORDER BY datetime(timestamp) DESC LIMIT ?"
        bind_values.append(int(limit))

        rows = []
        query = QSqlQuery()
        query.prepare(sql)
        for value in bind_values:
            query.addBindValue(value)

        if not query.exec():
            print("Activity log query failed:", query.lastError().text())
            return []

        while query.next():
            rows.append({
                "timestamp":      str(query.value(0) or ""),
                "username":       str(query.value(1) or ""),
                "category":       str(query.value(2) or ""),
                "action":         str(query.value(3) or ""),
                "entity_type":    str(query.value(4) or ""),
                "entity_id":      str(query.value(5) or ""),
                "note":           str(query.value(6) or ""),
                "previous_value": str(query.value(7) or ""),
                "new_value":      str(query.value(8) or ""),
            })

        return rows


    def get_summary_totals(self, date_from, date_to):
       

        def get_total(query_string, date_from, date_to):
            query = QSqlQuery()
            query.prepare(query_string)
            query.addBindValue(date_from)
            query.addBindValue(date_to)

            if query.exec() and query.next():
                value = query.value(0)
                if value == '':
                    value = None
                
                return float(value) if value is not None else 0.0

            return 0.0

        sales_query = """
            SELECT SUM(revenue_amount)
            FROM sales_item
            WHERE creation_date BETWEEN ? AND ?
        """

        purchase_query = """
            SELECT SUM(total)
            FROM purchase
            WHERE creation_date BETWEEN ? AND ?
        """

        expense_query = """
            SELECT SUM(amount)
            FROM expense
            WHERE creation_date BETWEEN ? AND ?
        """

        totals = {
            "sales": get_total(sales_query, date_from, date_to),
            "purchase": get_total(purchase_query, date_from, date_to),
            "expense": get_total(expense_query, date_from, date_to),
        }

        return totals
    
    
    
    
    def get_sales_summary(self, duration="today"):
        print("Fetching sales summary for duration:", duration)
        

        # Build WHERE clause using date ranges
        
        duration = duration.lower()
        if duration == "today":
            where_clause = "DATE(creation_date) = DATE('now')"
        elif duration == "week":
            # Last 7 days including today
            where_clause = "DATE(creation_date) >= DATE('now','-6 days')"
        elif duration == "month":
            # Last 30 days including today
            where_clause = "DATE(creation_date) >= DATE('now','-29 days')"
        elif duration == "year":
            # Last 1 year including today
            where_clause = "DATE(creation_date) >= DATE('now','-1 year')"
        elif duration == "all":
            where_clause = "1=1"
        else:
            print("Invalid duration. Use: today, week, month, year, all.")
            return 0, 0

        # Query total sales and invoice count
        query = QSqlQuery()
        sql = f"""
            SELECT IFNULL(SUM(total),0), COUNT(*)
            FROM sales
            WHERE {where_clause}
        """
        if not query.exec(sql):
            print("Query failed:", query.lastError().text())
            return 0, 0

        total_sales = 0
        total_invoices = 0
        if query.next():
            total_sales = query.value(0) or 0
            total_invoices = query.value(1) or 0

        return total_sales, total_invoices

    
    def get_purchase_summary(self, duration="today"):

        # Build WHERE clause using date ranges
        duration = duration.lower()
        if duration == "today":
            where_clause = "DATE(creation_date) = DATE('now')"
        elif duration == "week":
            where_clause = "DATE(creation_date) >= DATE('now','-6 days')"
        elif duration == "month":
            where_clause = "DATE(creation_date) >= DATE('now','-29 days')"
        elif duration == "year":
            where_clause = "DATE(creation_date) >= DATE('now','-1 year')"
        elif duration == "all":
            where_clause = "1=1"
        else:
            print("Invalid duration. Use: today, week, month, year, all.")
            return 0.0, 0

        # Query total purchases and invoice count
        query = QSqlQuery()
        sql = f"""
            SELECT IFNULL(SUM(total),0), COUNT(*)
            FROM purchase
            WHERE {where_clause}
        """
        if not query.exec(sql):
            print("Query failed:", query.lastError().text())
            return 0.0, 0

        total_purchase = 0.0
        total_invoices = 0
        if query.next():
            total_purchase = query.value(0) or 0.0
            total_invoices = query.value(1) or 0

        return total_purchase, total_invoices


    def get_expense_summary(self, duration="today"):

        # Build WHERE clause using date ranges
        duration = duration.lower()
        if duration == "today":
            where_clause = "DATE(creation_date) = DATE('now')"
        elif duration == "week":
            where_clause = "DATE(creation_date) >= DATE('now','-6 days')"
        elif duration == "month":
            where_clause = "DATE(creation_date) >= DATE('now','-29 days')"
        elif duration == "year":
            where_clause = "DATE(creation_date) >= DATE('now','-1 year')"
        elif duration == "all":
            where_clause = "1=1"
        else:
            print("Invalid duration. Use: today, week, month, year, all.")
            return 0.0, 0

        # Query total expenses and count of records
        query = QSqlQuery()
        sql = f"""
            SELECT IFNULL(SUM(amount),0), COUNT(*)
            FROM expense
            WHERE {where_clause}
        """
        if not query.exec(sql):
            print("Query failed:", query.lastError().text())
            return 0.0, 0

        total_expenses = 0.0
        num_records = 0
        if query.next():
            total_expenses = query.value(0) or 0.0
            num_records = query.value(1) or 0

        return total_expenses, num_records

   
        
        
            
   
    
    def get_detailed_revenue(self, duration="today"):
        """
        Returns:
            revenue_known_cost
            total_cogs
            gross_profit_known
            revenue_unknown_cost
            gross_margin_pct
            cost_coverage_pct
        """

        print("Fetching detailed revenue for duration:", duration)

        duration = duration.lower()

        if duration == "today":
            where_clause = "DATE(si.creation_date) = DATE('now')"
        elif duration == "week":
            where_clause = "DATE(si.creation_date) >= DATE('now','-6 days')"
        elif duration == "month":
            where_clause = "DATE(si.creation_date) >= DATE('now','-29 days')"
        elif duration == "year":
            where_clause = "DATE(si.creation_date) >= DATE('now','-1 year')"
        elif duration == "all":
            where_clause = "1=1"
        else:
            print("Invalid duration. Use: today, week, month, year, all.")
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        query = QSqlQuery()

        sql = f"""
            WITH sold_batch_rollup AS (
                SELECT
                    sb.sale_item_id,
                    SUM(CASE WHEN sb.unit_cost IS NOT NULL THEN COALESCE(sb.line_cost, 0) ELSE 0 END) AS known_cogs,
                    SUM(CASE WHEN sb.unit_cost IS NULL THEN 1 ELSE 0 END) AS unknown_cost_rows,
                    COUNT(*) AS batch_rows
                FROM sold_batch sb
                GROUP BY sb.sale_item_id
            )
            SELECT
                IFNULL(SUM(CASE
                    WHEN COALESCE(sbr.unknown_cost_rows, 0) = 0
                     AND COALESCE(sbr.batch_rows, 0) > 0
                    THEN COALESCE(si.effective_line_total, 0)
                    ELSE 0 END), 0) AS revenue_known,

                IFNULL(SUM(CASE
                    WHEN COALESCE(sbr.unknown_cost_rows, 0) = 0
                     AND COALESCE(sbr.batch_rows, 0) > 0
                    THEN COALESCE(sbr.known_cogs, 0)
                    ELSE 0 END), 0) AS total_cogs,

                IFNULL(SUM(CASE
                    WHEN COALESCE(sbr.unknown_cost_rows, 0) = 0
                     AND COALESCE(sbr.batch_rows, 0) > 0
                    THEN COALESCE(si.effective_line_total, 0) - COALESCE(sbr.known_cogs, 0)
                    ELSE 0 END), 0) AS gross_profit_known,

                IFNULL(SUM(CASE
                    WHEN COALESCE(sbr.unknown_cost_rows, 0) > 0
                      OR COALESCE(sbr.batch_rows, 0) = 0
                    THEN COALESCE(si.effective_line_total, 0)
                    ELSE 0 END), 0) AS revenue_unknown
            FROM salesitem si
            LEFT JOIN sold_batch_rollup sbr ON sbr.sale_item_id = si.id
            WHERE {where_clause}
        """

        if not query.exec(sql):
            print("Detailed revenue query failed:", query.lastError().text())
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        if query.next():
            revenue_known   = float(query.value(0) or 0.0)
            total_cogs      = float(query.value(1) or 0.0)
            gross_profit    = float(query.value(2) or 0.0)
            revenue_unknown = float(query.value(3) or 0.0)
            total_revenue = revenue_known + revenue_unknown

            gross_margin_pct = (gross_profit / revenue_known * 100.0) if revenue_known > 0 else 0.0
            cost_coverage_pct = (revenue_known / total_revenue * 100.0) if total_revenue > 0 else 0.0

            return revenue_known, total_cogs, gross_profit, revenue_unknown, gross_margin_pct, cost_coverage_pct

        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    def get_profit_audit_rows(self, duration="today", limit=200):
        """Return item-level profitability rows for audit (losses, margins, unknown-cost exposure)."""

        duration = (duration or "today").lower()
        if duration == "today":
            where_clause = "DATE(si.creation_date) = DATE('now')"
        elif duration == "week":
            where_clause = "DATE(si.creation_date) >= DATE('now','-6 days')"
        elif duration == "month":
            where_clause = "DATE(si.creation_date) >= DATE('now','-29 days')"
        elif duration == "year":
            where_clause = "DATE(si.creation_date) >= DATE('now','-1 year')"
        elif duration == "all":
            where_clause = "1=1"
        else:
            where_clause = "DATE(si.creation_date) = DATE('now')"

        try:
            limit = int(limit)
        except Exception:
            limit = 200
        if limit <= 0:
            limit = 200

        query = QSqlQuery()
        sql = f"""
            WITH sold_batch_rollup AS (
                SELECT
                    sb.sale_item_id,
                    SUM(CASE WHEN sb.unit_cost IS NOT NULL THEN COALESCE(sb.line_cost, 0) ELSE 0 END) AS known_cogs,
                    SUM(CASE WHEN sb.unit_cost IS NULL THEN 1 ELSE 0 END) AS unknown_cost_rows,
                    COUNT(*) AS batch_rows
                FROM sold_batch sb
                GROUP BY sb.sale_item_id
            ),
            line_audit AS (
                SELECT
                    COALESCE(si.product_id, 0) AS product_id,
                    COALESCE(p.display_name, 'Unknown Product') AS product_name,
                    COALESCE(si.qty_sold, 0) AS qty_sold,
                    CASE
                        WHEN COALESCE(sbr.unknown_cost_rows, 0) = 0
                         AND COALESCE(sbr.batch_rows, 0) > 0
                        THEN COALESCE(si.effective_line_total, 0)
                        ELSE 0
                    END AS known_revenue,
                    CASE
                        WHEN COALESCE(sbr.unknown_cost_rows, 0) = 0
                         AND COALESCE(sbr.batch_rows, 0) > 0
                        THEN COALESCE(sbr.known_cogs, 0)
                        ELSE 0
                    END AS known_cogs,
                    CASE
                        WHEN COALESCE(sbr.unknown_cost_rows, 0) > 0
                          OR COALESCE(sbr.batch_rows, 0) = 0
                        THEN COALESCE(si.effective_line_total, 0)
                        ELSE 0
                    END AS unknown_revenue
                FROM salesitem si
                LEFT JOIN sold_batch_rollup sbr ON sbr.sale_item_id = si.id
                LEFT JOIN product p ON p.id = si.product_id
                WHERE {where_clause}
            )
            SELECT
                product_id,
                product_name,
                SUM(qty_sold) AS qty_sold,
                SUM(known_revenue) AS known_revenue,
                SUM(known_cogs) AS known_cogs,
                SUM(known_revenue) - SUM(known_cogs) AS known_profit,
                SUM(unknown_revenue) AS unknown_revenue
            FROM line_audit
            GROUP BY product_id, product_name
            HAVING (SUM(known_revenue) + SUM(unknown_revenue)) > 0
            ORDER BY known_profit ASC, known_revenue DESC
            LIMIT {limit}
        """

        if not query.exec(sql):
            print("Profit audit query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            known_revenue = float(query.value(3) or 0.0)
            known_cogs = float(query.value(4) or 0.0)
            known_profit = float(query.value(5) or 0.0)
            unknown_revenue = float(query.value(6) or 0.0)
            total_revenue = known_revenue + unknown_revenue

            margin_pct = (known_profit / known_revenue * 100.0) if known_revenue > 0 else 0.0
            coverage_pct = (known_revenue / total_revenue * 100.0) if total_revenue > 0 else 0.0

            rows.append({
                "product_id": int(query.value(0) or 0),
                "product_name": str(query.value(1) or ""),
                "qty_sold": float(query.value(2) or 0.0),
                "known_revenue": known_revenue,
                "known_cogs": known_cogs,
                "known_profit": known_profit,
                "margin_pct": margin_pct,
                "unknown_revenue": unknown_revenue,
                "coverage_pct": coverage_pct,
            })

        return rows

    def get_product_profit_timeline(self, product_id, duration="all", group_by="day"):
        """Return period-wise profitability journey for a single product."""

        try:
            product_id = int(product_id)
        except Exception:
            return []

        duration = (duration or "all").lower()
        if duration == "today":
            where_clause = "DATE(si.creation_date) = DATE('now')"
        elif duration == "week":
            where_clause = "DATE(si.creation_date) >= DATE('now','-6 days')"
        elif duration == "month":
            where_clause = "DATE(si.creation_date) >= DATE('now','-29 days')"
        elif duration == "year":
            where_clause = "DATE(si.creation_date) >= DATE('now','-1 year')"
        elif duration == "all":
            where_clause = "1=1"
        else:
            where_clause = "1=1"

        group_by = (group_by or "day").lower()
        if group_by == "week":
            period_expr = "strftime('%Y-W%W', DATE(si.creation_date))"
        elif group_by == "month":
            period_expr = "strftime('%Y-%m', DATE(si.creation_date))"
        else:
            period_expr = "DATE(si.creation_date)"

        query = QSqlQuery()
        sql = f"""
            WITH sold_batch_rollup AS (
                SELECT
                    sb.sale_item_id,
                    SUM(CASE WHEN sb.unit_cost IS NOT NULL THEN COALESCE(sb.line_cost, 0) ELSE 0 END) AS known_cogs,
                    SUM(CASE WHEN sb.unit_cost IS NULL THEN 1 ELSE 0 END) AS unknown_cost_rows,
                    COUNT(*) AS batch_rows
                FROM sold_batch sb
                GROUP BY sb.sale_item_id
            ),
            line_audit AS (
                SELECT
                    {period_expr} AS period_key,
                    COALESCE(si.qty_sold, 0) AS qty_sold,
                    CASE
                        WHEN COALESCE(sbr.unknown_cost_rows, 0) = 0
                         AND COALESCE(sbr.batch_rows, 0) > 0
                        THEN COALESCE(si.effective_line_total, 0)
                        ELSE 0
                    END AS known_revenue,
                    CASE
                        WHEN COALESCE(sbr.unknown_cost_rows, 0) = 0
                         AND COALESCE(sbr.batch_rows, 0) > 0
                        THEN COALESCE(sbr.known_cogs, 0)
                        ELSE 0
                    END AS known_cogs,
                    CASE
                        WHEN COALESCE(sbr.unknown_cost_rows, 0) > 0
                          OR COALESCE(sbr.batch_rows, 0) = 0
                        THEN COALESCE(si.effective_line_total, 0)
                        ELSE 0
                    END AS unknown_revenue
                FROM salesitem si
                LEFT JOIN sold_batch_rollup sbr ON sbr.sale_item_id = si.id
                WHERE si.product_id = {product_id}
                  AND {where_clause}
            )
            SELECT
                period_key,
                SUM(qty_sold) AS qty_sold,
                SUM(known_revenue) AS known_revenue,
                SUM(known_cogs) AS known_cogs,
                SUM(unknown_revenue) AS unknown_revenue
            FROM line_audit
            GROUP BY period_key
            HAVING (SUM(known_revenue) + SUM(unknown_revenue)) > 0
            ORDER BY period_key ASC
        """

        if not query.exec(sql):
            print("Product profit timeline query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            known_revenue = float(query.value(2) or 0.0)
            known_cogs = float(query.value(3) or 0.0)
            unknown_revenue = float(query.value(4) or 0.0)
            known_profit = known_revenue - known_cogs
            total_revenue = known_revenue + unknown_revenue

            rows.append({
                "period": str(query.value(0) or ""),
                "qty_sold": float(query.value(1) or 0.0),
                "known_revenue": known_revenue,
                "known_cogs": known_cogs,
                "known_profit": known_profit,
                "margin_pct": (known_profit / known_revenue * 100.0) if known_revenue > 0 else 0.0,
                "unknown_revenue": unknown_revenue,
                "coverage_pct": (known_revenue / total_revenue * 100.0) if total_revenue > 0 else 0.0,
            })

        return rows
            
            
        
    
                
            
    def get_total_purchase_amount(self):

        from PySide6.QtSql import QSqlQuery

        query_string = """
            SELECT COALESCE(SUM(total), 0.0)
            FROM purchase
        """

        query = QSqlQuery()
        query.prepare(query_string)

        if query.exec() and query.next():
            value = query.value(0)
            print("Value is: ", value)
            return float(value) if value not in (None, '') else 0.0

        return 0.0
    
    
    

    
    def get_opening_estimate_amount(self):

        query_string = """
            SELECT opening_inventory_value
            FROM accounting_settings WHERE id=1
        """

        query = QSqlQuery()
        query.prepare(query_string)

        if query.exec() and query.next():
            value = query.value(0)
            print("Value is: ", value)
            return float(value) if value not in (None, '') else 0.0

        return 0.0
        
        
        
        
    def get_stock_count_alerts(self):
        

        today = QDate.currentDate()
        six_months_later = today.addMonths(6)

        def get_count(query_string, *params):
            query = QSqlQuery()
            query.prepare(query_string)

            for p in params:
                query.addBindValue(p)

            if query.exec() and query.next():
                value = query.value(0)
                return int(value) if value not in (None, '') else 0

            return 0

        # 1️⃣ Near Expiry Batches (within 6 months, still in stock)
        near_expiry_query = """
            SELECT COUNT(*)
            FROM (
                SELECT
                    quantity_remaining,
                    CASE
                        WHEN expiry_date LIKE '____-__-__' THEN date(expiry_date)
                        WHEN expiry_date LIKE '__-__-____'
                            THEN date(substr(expiry_date, 7, 4) || '-' || substr(expiry_date, 4, 2) || '-' || substr(expiry_date, 1, 2))
                        ELSE NULL
                    END AS expiry_norm
                FROM batch
                WHERE expiry_date IS NOT NULL
            ) x
            WHERE x.expiry_norm IS NOT NULL
            AND x.expiry_norm BETWEEN ? AND ?
            AND x.quantity_remaining > 0
        """

        near_expiry_batches = get_count(
            near_expiry_query,
            today.toString("yyyy-MM-dd"),
            six_months_later.toString("yyyy-MM-dd"),
        )

        # 2️⃣ Low Stock Products (total stock <= reorder level)
        low_stock_query = """
            SELECT COUNT(*)
            FROM (
                SELECT
                    p.id AS product_id,
                    COALESCE(SUM(b.quantity_remaining), 0) AS total_qty,
                    COALESCE(pp.reorder_level, 0) AS reorder_level
                FROM product p
                LEFT JOIN batch b ON b.product_id = p.id
                LEFT JOIN (
                    SELECT product_id, MAX(COALESCE(reorder_level, 0)) AS reorder_level
                    FROM price_pack
                    GROUP BY product_id
                ) pp ON pp.product_id = p.id
                WHERE p.status = 'used'
                GROUP BY p.id
                HAVING COALESCE(SUM(b.quantity_remaining), 0) <= MAX(COALESCE(pp.reorder_level, 0))
            )
        """

        low_stock_products = get_count(low_stock_query)

        return {
            "near_expiry_batches": near_expiry_batches,
            "low_stock_products": low_stock_products,
        }
        
           
        
        
    def get_supplier_balances(self):
        from PySide6.QtSql import QSqlQuery

        query = QSqlQuery()

        query_string = """
            SELECT 
                COALESCE(SUM(payable), 0),
                COALESCE(SUM(receiveable), 0)
            FROM supplier
        """

        if not query.exec(query_string):
            raise Exception(f"Supplier balance query failed: {query.lastError().text()}")

        if query.next():
            total_payable = query.value(0)
            total_receiveable = query.value(1)

            return float(total_payable), float(total_receiveable)

        return 0.0, 0.0
    
        
        
    def get_customer_balances(self):
        from PySide6.QtSql import QSqlQuery

        query = QSqlQuery()

        query_string = """
            SELECT 
                COALESCE(SUM(receiveable), 0),
                COALESCE(SUM(payable), 0)
            FROM customer
        """

        if not query.exec(query_string):
            raise Exception(f"Customer balance query failed: {query.lastError().text()}")

        if query.next():
            total_receivable = query.value(0)
            total_payable = query.value(1)

            return float(total_receivable), float(total_payable)

        return 0.0, 0.0

    def get_receivable_aging(self):
        """Return per-customer receivable aging buckets."""
        from PySide6.QtSql import QSqlQuery

        query = QSqlQuery()
        query_string = """
            WITH sales_open AS (
                SELECT
                    s.customer AS customer_id,
                    SUM(s.receiveable) AS total_due_sales,
                    SUM(CASE
                        WHEN s.due_date IS NOT NULL
                         AND julianday(s.due_date) >= julianday('now', 'localtime')
                        THEN s.receiveable ELSE 0 END) AS current_due,
                    SUM(CASE
                        WHEN s.due_date IS NOT NULL
                         AND julianday('now', 'localtime') - julianday(s.due_date) BETWEEN 1 AND 30
                        THEN s.receiveable ELSE 0 END) AS days_1_30,
                    SUM(CASE
                        WHEN s.due_date IS NOT NULL
                         AND julianday('now', 'localtime') - julianday(s.due_date) BETWEEN 31 AND 60
                        THEN s.receiveable ELSE 0 END) AS days_31_60,
                    SUM(CASE
                        WHEN s.due_date IS NOT NULL
                         AND julianday('now', 'localtime') - julianday(s.due_date) BETWEEN 61 AND 90
                        THEN s.receiveable ELSE 0 END) AS days_61_90,
                    SUM(CASE
                        WHEN s.due_date IS NOT NULL
                         AND julianday('now', 'localtime') - julianday(s.due_date) > 90
                        THEN s.receiveable ELSE 0 END) AS days_90plus,
                    SUM(CASE
                        WHEN s.due_date IS NULL THEN s.receiveable ELSE 0 END
                    ) AS no_due_date_sales
                FROM sales s
                WHERE s.customer IS NOT NULL
                  AND s.receiveable > 0
                  AND s.writeoff = 0
                GROUP BY s.customer
            )
            SELECT
                c.name AS customer_name,
                c.id AS customer_id,
                COALESCE(so.total_due_sales, 0)
                    + MAX(COALESCE(c.receiveable, 0) - COALESCE(so.total_due_sales, 0), 0) AS total_due,
                COALESCE(so.current_due, 0) AS current_due,
                COALESCE(so.days_1_30, 0) AS days_1_30,
                COALESCE(so.days_31_60, 0) AS days_31_60,
                COALESCE(so.days_61_90, 0) AS days_61_90,
                COALESCE(so.days_90plus, 0) AS days_90plus,
                COALESCE(so.no_due_date_sales, 0)
                    + MAX(COALESCE(c.receiveable, 0) - COALESCE(so.total_due_sales, 0), 0) AS no_due_date
            FROM customer c
            LEFT JOIN sales_open so ON so.customer_id = c.id
            WHERE COALESCE(c.receiveable, 0) > 0 OR COALESCE(so.total_due_sales, 0) > 0
            ORDER BY total_due DESC
        """

        if not query.exec(query_string):
            print("Receivable aging query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "customer_name": str(query.value(0) or ""),
                "customer_id":   query.value(1),
                "total_due":     float(query.value(2) or 0),
                "current_due":   float(query.value(3) or 0),
                "days_1_30":     float(query.value(4) or 0),
                "days_31_60":    float(query.value(5) or 0),
                "days_61_90":    float(query.value(6) or 0),
                "days_90plus":   float(query.value(7) or 0),
                "no_due_date":   float(query.value(8) or 0),
            })
        return rows

    def get_receivable_aging_invoices(self, customer_id):
        """Return individual outstanding invoices for a customer (drill-down)."""
        from PySide6.QtSql import QSqlQuery

        query = QSqlQuery()
        query.prepare("""
            SELECT
                s.id,
                DATE(s.creation_date)  AS invoice_date,
                s.total,
                s.received,
                s.receiveable,
                s.due_date,
                CASE
                    WHEN s.due_date IS NULL THEN 'No Due Date'
                    WHEN julianday(s.due_date) >= julianday('now', 'localtime') THEN 'Not Yet Due'
                    ELSE CAST(CAST(julianday('now', 'localtime') - julianday(s.due_date)
                              AS INTEGER) AS TEXT) || ' days overdue'
                END AS aging_status
            FROM sales s
            WHERE s.customer = ?
              AND s.receiveable > 0
              AND s.writeoff = 0
            ORDER BY s.due_date ASC NULLS LAST, s.creation_date ASC
        """)
        query.addBindValue(customer_id)

        if not query.exec():
            print("Invoice drill-down query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "invoice_id":    int(query.value(0) or 0),
                "invoice_date":  str(query.value(1) or ""),
                "total":         float(query.value(2) or 0),
                "received":      float(query.value(3) or 0),
                "receiveable":   float(query.value(4) or 0),
                "due_date":      str(query.value(5) or ""),
                "aging_status":  str(query.value(6) or ""),
            })
        return rows

    def get_receivable_forecast(self):
        """Return expected receivable collections grouped by due windows."""
        from PySide6.QtSql import QSqlQuery

        query = QSqlQuery()
        query_string = """
            WITH sales_open AS (
                SELECT
                    s.customer AS customer_id,
                    SUM(s.receiveable) AS total_due_sales,
                    SUM(CASE
                        WHEN s.due_date IS NOT NULL
                         AND julianday(s.due_date) < julianday('now', 'localtime')
                        THEN s.receiveable ELSE 0 END) AS overdue,
                    SUM(CASE
                        WHEN s.due_date IS NOT NULL
                         AND julianday(s.due_date) - julianday('now', 'localtime') BETWEEN 0 AND 7
                        THEN s.receiveable ELSE 0 END) AS due_0_7,
                    SUM(CASE
                        WHEN s.due_date IS NOT NULL
                         AND julianday(s.due_date) - julianday('now', 'localtime') BETWEEN 8 AND 15
                        THEN s.receiveable ELSE 0 END) AS due_8_15,
                    SUM(CASE
                        WHEN s.due_date IS NOT NULL
                         AND julianday(s.due_date) - julianday('now', 'localtime') BETWEEN 16 AND 30
                        THEN s.receiveable ELSE 0 END) AS due_16_30,
                    SUM(CASE
                        WHEN s.due_date IS NOT NULL
                         AND DATE(s.due_date) >= DATE('now', 'start of month', '+1 month')
                         AND DATE(s.due_date) < DATE('now', 'start of month', '+2 month')
                         AND julianday(s.due_date) - julianday('now', 'localtime') > 30
                        THEN s.receiveable ELSE 0 END) AS due_next_month,
                    SUM(CASE
                        WHEN s.due_date IS NOT NULL
                         AND julianday(s.due_date) - julianday('now', 'localtime') > 30
                         AND NOT (
                            DATE(s.due_date) >= DATE('now', 'start of month', '+1 month')
                            AND DATE(s.due_date) < DATE('now', 'start of month', '+2 month')
                         )
                        THEN s.receiveable ELSE 0 END) AS due_later,
                    SUM(CASE
                        WHEN s.due_date IS NULL THEN s.receiveable ELSE 0 END
                    ) AS no_due_date_sales
                FROM sales s
                WHERE s.customer IS NOT NULL
                  AND s.receiveable > 0
                  AND s.writeoff = 0
                GROUP BY s.customer
            )
            SELECT
                c.name AS customer_name,
                c.id AS customer_id,
                COALESCE(so.total_due_sales, 0)
                    + MAX(COALESCE(c.receiveable, 0) - COALESCE(so.total_due_sales, 0), 0) AS total_due,
                COALESCE(so.overdue, 0) AS overdue,
                COALESCE(so.due_0_7, 0) AS due_0_7,
                COALESCE(so.due_8_15, 0) AS due_8_15,
                COALESCE(so.due_16_30, 0) AS due_16_30,
                COALESCE(so.due_next_month, 0) AS due_next_month,
                COALESCE(so.due_later, 0) AS due_later,
                COALESCE(so.no_due_date_sales, 0)
                    + MAX(COALESCE(c.receiveable, 0) - COALESCE(so.total_due_sales, 0), 0) AS no_due_date
            FROM customer c
            LEFT JOIN sales_open so ON so.customer_id = c.id
            WHERE COALESCE(c.receiveable, 0) > 0 OR COALESCE(so.total_due_sales, 0) > 0
            ORDER BY total_due DESC
        """

        if not query.exec(query_string):
            print("Receivable forecast query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "customer_name": str(query.value(0) or ""),
                "customer_id":   query.value(1),
                "total_due":     float(query.value(2) or 0),
                "overdue":       float(query.value(3) or 0),
                "due_0_7":       float(query.value(4) or 0),
                "due_8_15":      float(query.value(5) or 0),
                "due_16_30":     float(query.value(6) or 0),
                "due_next_month": float(query.value(7) or 0),
                "due_later":     float(query.value(8) or 0),
                "no_due_date":   float(query.value(9) or 0),
            })
        return rows

    def get_receivable_forecast_invoices(self, customer_id):
        """Return outstanding invoices for a customer with forecast bucket labels."""
        from PySide6.QtSql import QSqlQuery

        query = QSqlQuery()
        query.prepare("""
            SELECT
                s.id,
                DATE(s.creation_date) AS invoice_date,
                s.total,
                s.received,
                s.receiveable,
                s.due_date,
                CASE
                    WHEN s.due_date IS NULL THEN 'No Due Date'
                    WHEN julianday(s.due_date) < julianday('now', 'localtime') THEN 'Overdue'
                    WHEN julianday(s.due_date) - julianday('now', 'localtime') BETWEEN 0 AND 7 THEN 'Due in 0-7 days'
                    WHEN julianday(s.due_date) - julianday('now', 'localtime') BETWEEN 8 AND 15 THEN 'Due in 8-15 days'
                    WHEN julianday(s.due_date) - julianday('now', 'localtime') BETWEEN 16 AND 30 THEN 'Due in 16-30 days'
                    WHEN DATE(s.due_date) >= DATE('now', 'start of month', '+1 month')
                     AND DATE(s.due_date) < DATE('now', 'start of month', '+2 month')
                     AND julianday(s.due_date) - julianday('now', 'localtime') > 30
                    THEN 'Due next month'
                    ELSE 'Due later'
                END AS forecast_bucket
            FROM sales s
            WHERE s.customer = ?
              AND s.receiveable > 0
              AND s.writeoff = 0
            ORDER BY s.due_date ASC NULLS LAST, s.creation_date ASC
        """)
        query.addBindValue(customer_id)

        if not query.exec():
            print("Receivable forecast invoice query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "invoice_id": int(query.value(0) or 0),
                "invoice_date": str(query.value(1) or ""),
                "total": float(query.value(2) or 0),
                "received": float(query.value(3) or 0),
                "receiveable": float(query.value(4) or 0),
                "due_date": str(query.value(5) or ""),
                "forecast_bucket": str(query.value(6) or ""),
            })
        return rows

    def get_supplier_payable_aging(self):
        """Return outstanding payables grouped by aging buckets (similar to customer aging)."""
        from PySide6.QtSql import QSqlQuery

        query = QSqlQuery()
        query_string = """
            WITH purchase_open AS (
                SELECT
                    p.supplier AS supplier_id,
                    SUM(p.payable) AS total_due_purchases,
                    SUM(CASE
                        WHEN p.due_date IS NOT NULL
                         AND julianday(p.due_date) >= julianday('now', 'localtime')
                        THEN p.payable ELSE 0 END) AS current_due,
                    SUM(CASE
                        WHEN p.due_date IS NOT NULL
                         AND julianday('now', 'localtime') - julianday(p.due_date) BETWEEN 1 AND 30
                        THEN p.payable ELSE 0 END) AS days_1_30,
                    SUM(CASE
                        WHEN p.due_date IS NOT NULL
                         AND julianday('now', 'localtime') - julianday(p.due_date) BETWEEN 31 AND 60
                        THEN p.payable ELSE 0 END) AS days_31_60,
                    SUM(CASE
                        WHEN p.due_date IS NOT NULL
                         AND julianday('now', 'localtime') - julianday(p.due_date) BETWEEN 61 AND 90
                        THEN p.payable ELSE 0 END) AS days_61_90,
                    SUM(CASE
                        WHEN p.due_date IS NOT NULL
                         AND julianday('now', 'localtime') - julianday(p.due_date) > 90
                        THEN p.payable ELSE 0 END) AS days_90plus,
                    SUM(CASE
                        WHEN p.due_date IS NULL THEN p.payable ELSE 0 END
                    ) AS no_due_date_purchases
                FROM purchase p
                WHERE p.supplier IS NOT NULL
                  AND p.payable > 0
                GROUP BY p.supplier
            )
            SELECT
                s.name AS supplier_name,
                s.id AS supplier_id,
                COALESCE(po.total_due_purchases, 0)
                    + MAX(COALESCE(s.payable, 0) - COALESCE(po.total_due_purchases, 0), 0) AS total_due,
                COALESCE(po.current_due, 0) AS current_due,
                COALESCE(po.days_1_30, 0) AS days_1_30,
                COALESCE(po.days_31_60, 0) AS days_31_60,
                COALESCE(po.days_61_90, 0) AS days_61_90,
                COALESCE(po.days_90plus, 0) AS days_90plus,
                COALESCE(po.no_due_date_purchases, 0)
                    + MAX(COALESCE(s.payable, 0) - COALESCE(po.total_due_purchases, 0), 0) AS no_due_date
            FROM supplier s
            LEFT JOIN purchase_open po ON po.supplier_id = s.id
            WHERE COALESCE(s.payable, 0) > 0 OR COALESCE(po.total_due_purchases, 0) > 0
            ORDER BY total_due DESC
        """

        if not query.exec(query_string):
            print("Supplier payable aging query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "supplier_name": str(query.value(0) or ""),
                "supplier_id":   query.value(1),
                "total_due":     float(query.value(2) or 0),
                "current_due":   float(query.value(3) or 0),
                "days_1_30":     float(query.value(4) or 0),
                "days_31_60":    float(query.value(5) or 0),
                "days_61_90":    float(query.value(6) or 0),
                "days_90plus":   float(query.value(7) or 0),
                "no_due_date":   float(query.value(8) or 0),
            })
        return rows

    def get_supplier_payable_aging_invoices(self, supplier_id):
        """Return individual outstanding purchase invoices for a supplier (drill-down)."""
        from PySide6.QtSql import QSqlQuery

        query = QSqlQuery()
        query.prepare("""
            SELECT
                p.id,
                DATE(p.creation_date) AS invoice_date,
                p.total,
                p.paid,
                p.payable,
                p.due_date,
                CASE
                    WHEN p.due_date IS NULL THEN 'No Due Date'
                    WHEN julianday(p.due_date) >= julianday('now', 'localtime') THEN 'Not Yet Due'
                    ELSE CAST(CAST(julianday('now', 'localtime') - julianday(p.due_date)
                              AS INTEGER) AS TEXT) || ' days overdue'
                END AS aging_status
            FROM purchase p
            WHERE p.supplier = ?
              AND p.payable > 0
            ORDER BY p.due_date ASC NULLS LAST, p.creation_date ASC
        """)
        query.addBindValue(supplier_id)

        if not query.exec():
            print("Supplier invoice drill-down query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "invoice_id":    int(query.value(0) or 0),
                "invoice_date":  str(query.value(1) or ""),
                "total":         float(query.value(2) or 0),
                "paid":          float(query.value(3) or 0),
                "payable":       float(query.value(4) or 0),
                "due_date":      str(query.value(5) or ""),
                "aging_status":  str(query.value(6) or ""),
            })
        return rows

    def get_supplier_payable_forecast(self):
        """Return expected supplier payment obligations grouped by due windows."""
        from PySide6.QtSql import QSqlQuery

        query = QSqlQuery()
        query_string = """
            WITH purchase_open AS (
                SELECT
                    p.supplier AS supplier_id,
                    SUM(p.payable) AS total_due_purchases,
                    SUM(CASE
                        WHEN p.due_date IS NOT NULL
                         AND julianday(p.due_date) < julianday('now', 'localtime')
                        THEN p.payable ELSE 0 END) AS overdue,
                    SUM(CASE
                        WHEN p.due_date IS NOT NULL
                         AND julianday(p.due_date) - julianday('now', 'localtime') BETWEEN 0 AND 7
                        THEN p.payable ELSE 0 END) AS due_0_7,
                    SUM(CASE
                        WHEN p.due_date IS NOT NULL
                         AND julianday(p.due_date) - julianday('now', 'localtime') BETWEEN 8 AND 15
                        THEN p.payable ELSE 0 END) AS due_8_15,
                    SUM(CASE
                        WHEN p.due_date IS NOT NULL
                         AND julianday(p.due_date) - julianday('now', 'localtime') BETWEEN 16 AND 30
                        THEN p.payable ELSE 0 END) AS due_16_30,
                    SUM(CASE
                        WHEN p.due_date IS NOT NULL
                         AND DATE(p.due_date) >= DATE('now', 'start of month', '+1 month')
                         AND DATE(p.due_date) < DATE('now', 'start of month', '+2 month')
                         AND julianday(p.due_date) - julianday('now', 'localtime') > 30
                        THEN p.payable ELSE 0 END) AS due_next_month,
                    SUM(CASE
                        WHEN p.due_date IS NOT NULL
                         AND julianday(p.due_date) - julianday('now', 'localtime') > 30
                         AND NOT (
                            DATE(p.due_date) >= DATE('now', 'start of month', '+1 month')
                            AND DATE(p.due_date) < DATE('now', 'start of month', '+2 month')
                         )
                        THEN p.payable ELSE 0 END) AS due_later,
                    SUM(CASE
                        WHEN p.due_date IS NULL THEN p.payable ELSE 0 END
                    ) AS no_due_date_purchases
                FROM purchase p
                WHERE p.supplier IS NOT NULL
                  AND p.payable > 0
                GROUP BY p.supplier
            )
            SELECT
                s.name AS supplier_name,
                s.id AS supplier_id,
                COALESCE(po.total_due_purchases, 0)
                    + MAX(COALESCE(s.payable, 0) - COALESCE(po.total_due_purchases, 0), 0) AS total_due,
                COALESCE(po.overdue, 0) AS overdue,
                COALESCE(po.due_0_7, 0) AS due_0_7,
                COALESCE(po.due_8_15, 0) AS due_8_15,
                COALESCE(po.due_16_30, 0) AS due_16_30,
                COALESCE(po.due_next_month, 0) AS due_next_month,
                COALESCE(po.due_later, 0) AS due_later,
                COALESCE(po.no_due_date_purchases, 0)
                    + MAX(COALESCE(s.payable, 0) - COALESCE(po.total_due_purchases, 0), 0) AS no_due_date
            FROM supplier s
            LEFT JOIN purchase_open po ON po.supplier_id = s.id
            WHERE COALESCE(s.payable, 0) > 0 OR COALESCE(po.total_due_purchases, 0) > 0
            ORDER BY total_due DESC
        """

        if not query.exec(query_string):
            print("Supplier payable forecast query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "supplier_name": str(query.value(0) or ""),
                "supplier_id":   query.value(1),
                "total_due":     float(query.value(2) or 0),
                "overdue":       float(query.value(3) or 0),
                "due_0_7":       float(query.value(4) or 0),
                "due_8_15":      float(query.value(5) or 0),
                "due_16_30":     float(query.value(6) or 0),
                "due_next_month": float(query.value(7) or 0),
                "due_later":     float(query.value(8) or 0),
                "no_due_date":   float(query.value(9) or 0),
            })
        return rows

    def get_supplier_payable_forecast_invoices(self, supplier_id):
        """Return outstanding purchase invoices for a supplier with forecast bucket labels."""
        from PySide6.QtSql import QSqlQuery

        query = QSqlQuery()
        query.prepare("""
            SELECT
                p.id,
                DATE(p.creation_date) AS invoice_date,
                p.total,
                p.paid,
                p.payable,
                p.due_date,
                CASE
                    WHEN p.due_date IS NULL THEN 'No Due Date'
                    WHEN julianday(p.due_date) < julianday('now', 'localtime') THEN 'Overdue'
                    WHEN julianday(p.due_date) - julianday('now', 'localtime') BETWEEN 0 AND 7 THEN 'Due in 0-7 days'
                    WHEN julianday(p.due_date) - julianday('now', 'localtime') BETWEEN 8 AND 15 THEN 'Due in 8-15 days'
                    WHEN julianday(p.due_date) - julianday('now', 'localtime') BETWEEN 16 AND 30 THEN 'Due in 16-30 days'
                    WHEN DATE(p.due_date) >= DATE('now', 'start of month', '+1 month')
                     AND DATE(p.due_date) < DATE('now', 'start of month', '+2 month')
                     AND julianday(p.due_date) - julianday('now', 'localtime') > 30
                    THEN 'Due next month'
                    ELSE 'Due later'
                END AS forecast_bucket
            FROM purchase p
            WHERE p.supplier = ?
              AND p.payable > 0
            ORDER BY p.due_date ASC NULLS LAST, p.creation_date ASC
        """)
        query.addBindValue(supplier_id)

        if not query.exec():
            print("Supplier payable forecast invoice query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "invoice_id": int(query.value(0) or 0),
                "invoice_date": str(query.value(1) or ""),
                "total": float(query.value(2) or 0),
                "paid": float(query.value(3) or 0),
                "payable": float(query.value(4) or 0),
                "due_date": str(query.value(5) or ""),
                "forecast_bucket": str(query.value(6) or ""),
            })
        return rows
        
        
        
