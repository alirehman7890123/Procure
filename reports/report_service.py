
from PySide6.QtSql import  QSqlQuery
from PySide6.QtCore import QDate
from services.accounting_settings_service import load_opening_inventory_value



class ReportService:
    @staticmethod
    def _to_float(value, default=0.0):
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        if not text:
            return default

        text = text.replace(",", "")
        if text in {"-", ".", "-.", "+", "+"}:
            return default

        try:
            return float(text)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _to_optional_float(cls, value):
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return cls._to_float(value, default=None)

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

    def get_inventory_overview_snapshot(self):
        inventory = self.get_current_inventory_snapshot()
        sale_snapshot = self.get_current_inventory_sale_snapshot()
        return {
            "inventory": inventory,
            "opening_estimate_amount": float(self.get_opening_estimate_amount() or 0.0),
            "known_stock_cost_amount": float(self.get_total_purchase_amount() or 0.0),
            "potential_stock_sale_amount": float(sale_snapshot.get("known_sale_value", 0.0) or 0.0),
            "unknown_sale_price_units": float(sale_snapshot.get("unknown_price_units", 0.0) or 0.0),
            "projected_stock_margin_amount": (
                float(sale_snapshot.get("known_sale_value", 0.0) or 0.0)
                - float(inventory.get("known_inventory_value", 0.0) or 0.0)
            ),
            "stock_alerts": self.get_stock_count_alerts(),
        }

    def get_current_inventory_sale_snapshot(self):
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                COALESCE(SUM(
                    COALESCE(b.quantity_remaining, 0) * COALESCE((
                        SELECT pp.unit_price
                        FROM price_pack pp
                        WHERE pp.product_id = b.product_id
                        ORDER BY pp.is_default DESC, pp.id DESC
                        LIMIT 1
                    ), 0)
                ), 0) AS known_sale_value,
                COALESCE(SUM(
                    CASE
                        WHEN COALESCE((
                            SELECT pp.unit_price
                            FROM price_pack pp
                            WHERE pp.product_id = b.product_id
                            ORDER BY pp.is_default DESC, pp.id DESC
                            LIMIT 1
                        ), 0) <= 0
                        THEN COALESCE(b.quantity_remaining, 0)
                        ELSE 0
                    END
                ), 0) AS unknown_price_units
            FROM batch b
            WHERE COALESCE(b.quantity_remaining, 0) > 0
            """
        )

        if not query.exec():
            print("Current inventory sale snapshot query failed:", query.lastError().text())
            return {
                "known_sale_value": 0.0,
                "unknown_price_units": 0.0,
            }

        if query.next():
            return {
                "known_sale_value": float(query.value(0) or 0.0),
                "unknown_price_units": float(query.value(1) or 0.0),
            }

        return {
            "known_sale_value": 0.0,
            "unknown_price_units": 0.0,
        }

    def get_balance_sheet_snapshot(self):
        inventory = self.get_current_inventory_snapshot()
        session_cash = self.get_latest_session_cash_position()
        opening_estimate = float(self.get_opening_estimate_amount() or 0.0)
        supplier_payable, supplier_receiveable = self.get_supplier_balances()
        customer_receivable, customer_payable = self.get_customer_balances()

        known_current_assets = (
            float(session_cash.get("cash_value", 0.0) or 0.0)
            + float(customer_receivable or 0.0)
            + float(supplier_receiveable or 0.0)
            + float(inventory.get("known_inventory_value", 0.0) or 0.0)
        )
        current_liabilities = float(supplier_payable or 0.0) + float(customer_payable or 0.0)

        return {
            "inventory": inventory,
            "session_cash": session_cash,
            "opening_estimate_amount": opening_estimate,
            "supplier_payable": float(supplier_payable or 0.0),
            "supplier_receiveable": float(supplier_receiveable or 0.0),
            "customer_receivable": float(customer_receivable or 0.0),
            "customer_payable": float(customer_payable or 0.0),
            "known_current_assets": known_current_assets,
            "current_liabilities": current_liabilities,
            "working_capital": known_current_assets - current_liabilities,
        }

    def get_trial_balance_snapshot(self):
        inventory = self.get_current_inventory_snapshot()
        session_cash = self.get_latest_session_cash_position()
        supplier_payable, supplier_receiveable = self.get_supplier_balances()
        customer_receivable, customer_payable = self.get_customer_balances()

        rows = [
            {
                "account": "Cash on Hand",
                "debit": float(session_cash.get("cash_value", 0.0) or 0.0),
                "credit": 0.0,
                "note": session_cash.get("label", "Latest session cash"),
            },
            {
                "account": "Inventory at Known Cost",
                "debit": float(inventory.get("known_inventory_value", 0.0) or 0.0),
                "credit": 0.0,
                "note": "Only stock with known unit cost is included.",
            },
            {
                "account": "Customer Receivables",
                "debit": float(customer_receivable or 0.0),
                "credit": 0.0,
                "note": "Amounts receivable from customers.",
            },
            {
                "account": "Supplier Receivables / Advances",
                "debit": float(supplier_receiveable or 0.0),
                "credit": 0.0,
                "note": "Advances or balances due back from suppliers.",
            },
            {
                "account": "Supplier Payables",
                "debit": 0.0,
                "credit": float(supplier_payable or 0.0),
                "note": "Outstanding supplier obligations.",
            },
            {
                "account": "Customer Payables / Advances",
                "debit": 0.0,
                "credit": float(customer_payable or 0.0),
                "note": "Customer credit balances or amounts payable.",
            },
        ]

        total_debit = sum(row["debit"] for row in rows)
        total_credit = sum(row["credit"] for row in rows)
        balancing = total_debit - total_credit

        if balancing > 0:
            rows.append({
                "account": "Unclassified Equity / Capital",
                "debit": 0.0,
                "credit": balancing,
                "note": "Balancing figure for capital, retained earnings, and other accounts not yet modeled.",
            })
        elif balancing < 0:
            rows.append({
                "account": "Unclassified Equity / Capital",
                "debit": abs(balancing),
                "credit": 0.0,
                "note": "Balancing figure for capital, retained earnings, and other accounts not yet modeled.",
            })

        total_debit = sum(row["debit"] for row in rows)
        total_credit = sum(row["credit"] for row in rows)

        return {
            "inventory": inventory,
            "rows": rows,
            "total_debit": total_debit,
            "total_credit": total_credit,
        }

    def get_cash_flow_snapshot(self, duration="today"):
        cash_flow = self.get_cash_flow_summary(duration)
        session_cash = self.get_latest_session_cash_position()
        session_label = session_cash.get("label", "Latest Session Cash")

        return {
            "duration": duration,
            "cash_flow": cash_flow,
            "session_cash": session_cash,
            "session_label": session_label,
            "notes": [
                f"Customer cash rows: {int(cash_flow.get('customer_rows', 0) or 0)} | Supplier cash rows: {int(cash_flow.get('supplier_rows', 0) or 0)} | Cash expense rows: {int(cash_flow.get('expense_rows', 0) or 0)}",
                "This report tracks cash-method activity only. Bank, wallet, and other non-cash methods are outside this cash movement view.",
                "Session cash is shown as a current operational reference, not as a period opening/closing reconciliation statement.",
            ],
        }

    def get_profit_loss_snapshot(self, duration="today"):
        revenue_known, total_cogs, gross_profit, revenue_unknown, gross_margin_pct, coverage_pct = self.get_detailed_revenue(duration)
        total_expenses, expense_count = self.get_expense_summary(duration)
        total_revenue = revenue_known + revenue_unknown
        net_profit = gross_profit - total_expenses
        net_margin_pct = (net_profit / total_revenue * 100.0) if total_revenue > 0 else 0.0

        return {
            "duration": duration,
            "revenue_known": revenue_known,
            "total_cogs": total_cogs,
            "gross_profit": gross_profit,
            "revenue_unknown": revenue_unknown,
            "gross_margin_pct": gross_margin_pct,
            "coverage_pct": coverage_pct,
            "total_expenses": total_expenses,
            "expense_count": int(expense_count or 0),
            "total_revenue": total_revenue,
            "net_profit": net_profit,
            "net_margin_pct": net_margin_pct,
            "notes": [
                "Known Gross Profit uses only sale lines where all consumed stock had a known cost.",
                "Revenue With Unknown Cost is excluded from profit until opening stock or batch cost is assigned.",
                f"Expense records in period: {int(expense_count or 0)}",
            ],
        }

    def get_overview_totals_snapshot(self, duration="today"):
        total_sales, total_invoices = self.get_sales_summary(duration)
        total_purchase, purchase_invoices = self.get_purchase_summary(duration)
        total_expenses, expense_records = self.get_expense_summary(duration)
        profit_snapshot = self.get_profit_loss_snapshot(duration)

        return {
            "duration": duration,
            "total_sales": float(total_sales or 0.0),
            "total_sales_invoices": int(total_invoices or 0),
            "total_purchase": float(total_purchase or 0.0),
            "total_purchase_invoices": int(purchase_invoices or 0),
            "total_expenses": float(total_expenses or 0.0),
            "expense_records": int(expense_records or 0),
            "profit_snapshot": profit_snapshot,
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

    def get_customer_outstanding_rows(self):
        query = QSqlQuery()
        sql = """
            SELECT
                COALESCE(name, 'Walk-in Customer') AS customer_name,
                COALESCE(receiveable, 0) AS receivable,
                COALESCE(payable, 0) AS payable
            FROM customer
            WHERE COALESCE(receiveable, 0) > 0 OR COALESCE(payable, 0) > 0
            ORDER BY COALESCE(receiveable, 0) DESC, COALESCE(payable, 0) DESC, name ASC
        """
        if not query.exec(sql):
            print("Customer outstanding query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            receivable = float(query.value(1) or 0.0)
            payable = float(query.value(2) or 0.0)
            rows.append({
                "customer_name": str(query.value(0) or ""),
                "receivable": receivable,
                "payable": payable,
                "net_exposure": receivable - payable,
            })
        return rows

    def get_supplier_outstanding_rows(self):
        query = QSqlQuery()
        sql = """
            SELECT
                COALESCE(name, 'Unknown Supplier') AS supplier_name,
                COALESCE(payable, 0) AS payable,
                COALESCE(receiveable, 0) AS receivable
            FROM supplier
            WHERE COALESCE(payable, 0) > 0 OR COALESCE(receiveable, 0) > 0
            ORDER BY COALESCE(payable, 0) DESC, COALESCE(receiveable, 0) DESC, name ASC
        """
        if not query.exec(sql):
            print("Supplier outstanding query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            payable = float(query.value(1) or 0.0)
            receivable = float(query.value(2) or 0.0)
            rows.append({
                "supplier_name": str(query.value(0) or ""),
                "payable": payable,
                "receivable": receivable,
                "net_exposure": payable - receivable,
            })
        return rows

    def get_used_product_options(self):
        query = QSqlQuery()
        query.prepare("""
            SELECT id, display_name
            FROM product
            WHERE status = 'used'
            ORDER BY display_name ASC
        """)
        if not query.exec():
            print("Used product options query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "product_id": int(query.value(0) or 0),
                "display_name": str(query.value(1) or ""),
            })
        return rows

    def get_hourly_sales_data(self):
        from datetime import datetime

        local_offset = datetime.now().astimezone().utcoffset()
        offset_hours = int(local_offset.total_seconds() // 3600)
        offset_str = f"{offset_hours:+d} hours"
        today = datetime.now().strftime('%Y-%m-%d')
        hourly_sales = {i: 0 for i in range(24)}

        query = QSqlQuery()
        query.prepare("""
            SELECT 
                strftime('%H', datetime(creation_date, :offset)) AS hour,
                COALESCE(SUM(total), 0) AS total_sales
            FROM sales
            WHERE 
                date(datetime(creation_date, :offset)) = date(:today)
            GROUP BY hour
            ORDER BY hour
        """)
        query.bindValue(":offset", offset_str)
        query.bindValue(":today", today)

        if query.exec():
            while query.next():
                hour = int(query.value(0) or 0)
                total = float(query.value(1) or 0.0)
                hourly_sales[hour] = total
        else:
            print("Hourly sales query failed:", query.lastError().text())

        return hourly_sales

    def get_monthly_sales_data(self):
        monthly_sales = {day: 0 for day in range(1, 32)}

        query = QSqlQuery()
        query.prepare("""
            WITH RECURSIVE days(day) AS (
                SELECT 1
                UNION ALL
                SELECT day + 1 FROM days WHERE day < 31
            )
            SELECT
                days.day,
                COALESCE(SUM(s.total), 0) AS total_sales
            FROM
                days
            LEFT JOIN
                sales s
                ON CAST(STRFTIME('%d', s.creation_date) AS INTEGER) = days.day
                AND STRFTIME('%Y-%m', s.creation_date) = STRFTIME('%Y-%m', 'now')
            GROUP BY
                days.day
            ORDER BY
                days.day
        """)

        if query.exec():
            while query.next():
                day = int(query.value(0) or 0)
                total = float(query.value(1) or 0.0)
                monthly_sales[day] = total
        else:
            print("Monthly sales query failed:", query.lastError().text())

        return monthly_sales

    def get_business_name(self):
        query = QSqlQuery()
        query.prepare("SELECT businessname FROM business WHERE id = 1")
        if query.exec() and query.next():
            return str(query.value(0) or "ProCure Medics")
        return "ProCure Medics"

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

    def get_payroll_register_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("COALESCE(p.paid_on, p.creation_date)", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                p.id,
                DATE(COALESCE(p.paid_on, p.creation_date)) AS paid_on,
                COALESCE(p.month, '') AS salary_month,
                COALESCE(e.name, 'Unknown Employee') AS employee_name,
                COALESCE(p.basic_salary, 0),
                COALESCE(p.allowances, 0),
                COALESCE(p.deductions, 0),
                COALESCE(p.advance_deduct, 0),
                COALESCE(p.net_salary, 0),
                COALESCE(p.payment_method, ''),
                COALESCE(p.status, '')
            FROM payroll p
            LEFT JOIN employee e ON e.id = p.employee_id
            WHERE {where_clause}
            ORDER BY DATE(COALESCE(p.paid_on, p.creation_date)) DESC, p.id DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Payroll register rows query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "payroll_id": int(query.value(0) or 0),
                "paid_on": str(query.value(1) or ""),
                "salary_month": str(query.value(2) or ""),
                "employee_name": str(query.value(3) or ""),
                "basic_salary": float(query.value(4) or 0.0),
                "allowances": float(query.value(5) or 0.0),
                "deductions": float(query.value(6) or 0.0),
                "advance_deduct": float(query.value(7) or 0.0),
                "net_salary": float(query.value(8) or 0.0),
                "payment_method": str(query.value(9) or ""),
                "status": str(query.value(10) or ""),
            })
        return rows

    def get_attendance_summary_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("a.date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                COALESCE(e.id, 0),
                COALESCE(e.name, 'Unknown Employee') AS employee_name,
                COALESCE(SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END), 0) AS present,
                COALESCE(SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END), 0) AS absent,
                COALESCE(SUM(CASE WHEN a.status = 'half_day' THEN 1 ELSE 0 END), 0) AS half_day,
                COALESCE(SUM(CASE WHEN a.status = 'leave' THEN 1 ELSE 0 END), 0) AS leave,
                COALESCE(COUNT(a.id), 0) AS total_marked
            FROM attendance a
            LEFT JOIN employee e ON e.id = a.employee_id
            WHERE {where_clause}
            GROUP BY e.id, e.name
            ORDER BY employee_name ASC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Attendance summary rows query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "employee_id": int(query.value(0) or 0),
                "employee_name": str(query.value(1) or ""),
                "present": int(query.value(2) or 0),
                "absent": int(query.value(3) or 0),
                "half_day": int(query.value(4) or 0),
                "leave": int(query.value(5) or 0),
                "total_marked": int(query.value(6) or 0),
            })
        return rows

    def get_salary_advance_outstanding_rows(self, duration="today", limit=500):
        where_clause = self._duration_where("sa.date", duration)
        query = QSqlQuery()
        sql = f"""
            SELECT
                sa.id,
                DATE(sa.date) AS advance_date,
                COALESCE(e.name, 'Unknown Employee') AS employee_name,
                COALESCE(sa.amount, 0),
                COALESCE(sa.recovered, 0),
                (COALESCE(sa.amount, 0) - COALESCE(sa.recovered, 0)) AS outstanding,
                COALESCE(sa.status, ''),
                COALESCE(sa.reason, '')
            FROM salary_advance sa
            LEFT JOIN employee e ON e.id = sa.employee_id
            WHERE {where_clause}
              AND (COALESCE(sa.amount, 0) - COALESCE(sa.recovered, 0)) > 0
            ORDER BY DATE(sa.date) DESC, sa.id DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Salary advance outstanding rows query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            rows.append({
                "advance_id": int(query.value(0) or 0),
                "advance_date": str(query.value(1) or ""),
                "employee_name": str(query.value(2) or ""),
                "amount": float(query.value(3) or 0.0),
                "recovered": float(query.value(4) or 0.0),
                "outstanding": float(query.value(5) or 0.0),
                "status": str(query.value(6) or ""),
                "reason": str(query.value(7) or ""),
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

    def get_stock_sale_value_rows(self, limit=1000):
        query = QSqlQuery()
        sql = f"""
            SELECT
                COALESCE(p.id, 0),
                COALESCE(p.display_name, 'Unknown Product') AS product_name,
                COALESCE(SUM(CASE WHEN COALESCE(b.quantity_remaining, 0) > 0 THEN COALESCE(b.quantity_remaining, 0) ELSE 0 END), 0) AS stock_qty,
                COALESCE(SUM(CASE
                    WHEN COALESCE(b.quantity_remaining, 0) > 0
                     AND COALESCE((
                        SELECT pp.unit_price
                        FROM price_pack pp
                        WHERE pp.product_id = p.id
                        ORDER BY pp.is_default DESC, pp.id DESC
                        LIMIT 1
                     ), 0) > 0
                    THEN COALESCE(b.quantity_remaining, 0) * COALESCE((
                        SELECT pp.unit_price
                        FROM price_pack pp
                        WHERE pp.product_id = p.id
                        ORDER BY pp.is_default DESC, pp.id DESC
                        LIMIT 1
                    ), 0)
                    ELSE 0
                END), 0) AS sale_value,
                COALESCE(SUM(CASE
                    WHEN COALESCE(b.quantity_remaining, 0) > 0
                     AND b.unit_cost IS NOT NULL
                    THEN COALESCE(b.quantity_remaining, 0) * COALESCE(b.unit_cost, 0)
                    ELSE 0
                END), 0) AS known_cost_value,
                COALESCE(SUM(CASE
                    WHEN COALESCE(b.quantity_remaining, 0) > 0
                     AND COALESCE((
                        SELECT pp.unit_price
                        FROM price_pack pp
                        WHERE pp.product_id = p.id
                        ORDER BY pp.is_default DESC, pp.id DESC
                        LIMIT 1
                     ), 0) <= 0
                    THEN COALESCE(b.quantity_remaining, 0)
                    ELSE 0
                END), 0) AS unknown_sale_price_units,
                COALESCE(SUM(CASE
                    WHEN COALESCE(b.quantity_remaining, 0) > 0
                     AND b.unit_cost IS NULL
                    THEN COALESCE(b.quantity_remaining, 0)
                    ELSE 0
                END), 0) AS unknown_cost_units
            FROM product p
            LEFT JOIN batch b ON b.product_id = p.id
            WHERE p.status = 'used'
            GROUP BY p.id, p.display_name
            HAVING stock_qty > 0
            ORDER BY sale_value DESC, stock_qty DESC
            LIMIT {int(limit)}
        """
        if not query.exec(sql):
            print("Stock sale value query failed:", query.lastError().text())
            return []

        rows = []
        while query.next():
            sale_value = float(query.value(3) or 0.0)
            known_cost_value = float(query.value(4) or 0.0)
            rows.append({
                "product_id": int(query.value(0) or 0),
                "product_name": str(query.value(1) or ""),
                "stock_qty": float(query.value(2) or 0.0),
                "sale_value": sale_value,
                "known_cost_value": known_cost_value,
                "projected_margin": sale_value - known_cost_value,
                "unknown_sale_price_units": float(query.value(5) or 0.0),
                "unknown_cost_units": float(query.value(6) or 0.0),
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

    def get_batch_reference_details(self, batch_id):
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                b.id,
                COALESCE(b.batch_no, ''),
                COALESCE(p.display_name, ''),
                COALESCE(b.expiry_date, ''),
                COALESCE(b.total_received, 0),
                COALESCE(b.quantity_remaining, 0),
                COALESCE(b.received_at, ''),
                COALESCE(b.source, '')
            FROM batch b
            LEFT JOIN product p ON p.id = b.product_id
            WHERE b.id = ?
            LIMIT 1
            """
        )
        query.addBindValue(batch_id)

        if query.exec() and query.next():
            return [
                ("Batch ID", query.value(0)),
                ("Batch No", query.value(1)),
                ("Product", query.value(2)),
                ("Expiry", query.value(3)),
                ("Total Received", query.value(4)),
                ("Remaining", query.value(5)),
                ("Received At", query.value(6)),
                ("Source", query.value(7)),
            ]

        return None

    def get_sales_reference_details(self, sales_id):
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                s.id,
                s.creation_date,
                COALESCE(s.total, 0),
                COALESCE(a.username, ''),
                COALESCE(c.name, '')
            FROM sales s
            LEFT JOIN auth a ON a.id = s.salesman
            LEFT JOIN customer c ON c.id = s.customer
            WHERE s.id = ?
            LIMIT 1
            """
        )
        query.addBindValue(sales_id)

        if query.exec() and query.next():
            return [
                ("Sales ID", query.value(0)),
                ("Date", query.value(1)),
                ("Total", query.value(2)),
                ("Salesman", query.value(3)),
                ("Customer", query.value(4)),
            ]

        return None

    def get_sales_return_reference_details(self, return_id):
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                sr.id,
                sr.creation_date,
                COALESCE(sr.total, 0),
                COALESCE(sr.salesorder, 0)
            FROM salesreturn sr
            WHERE sr.id = ?
            LIMIT 1
            """
        )
        query.addBindValue(return_id)

        if query.exec() and query.next():
            return [
                ("Sales Return ID", query.value(0)),
                ("Date", query.value(1)),
                ("Total", query.value(2)),
                ("Sales Order", query.value(3)),
            ]

        return None

    def get_purchase_return_reference_details(self, return_id):
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                pr.id,
                pr.creation_date,
                COALESCE(pr.total, 0),
                COALESCE(s.name, '')
            FROM purchase_return pr
            LEFT JOIN supplier s ON s.id = pr.supplier
            WHERE pr.id = ?
            LIMIT 1
            """
        )
        query.addBindValue(return_id)

        if query.exec() and query.next():
            return [
                ("Purchase Return ID", query.value(0)),
                ("Date", query.value(1)),
                ("Total", query.value(2)),
                ("Supplier", query.value(3)),
            ]

        return None

    def get_adjustment_reference_details(self, adjustment_id):
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                ia.id,
                ia.created_at,
                COALESCE(ia.adjustment_type, ''),
                COALESCE(ia.qty, 0),
                COALESCE(ia.old_qty, 0),
                COALESCE(ia.new_qty, 0),
                COALESCE(ia.reason, ''),
                COALESCE(a.username, ''),
                COALESCE(b.batch_no, '')
            FROM inventory_adjustment ia
            LEFT JOIN auth a ON a.id = ia.adjusted_by
            LEFT JOIN batch b ON b.id = ia.batch_id
            WHERE ia.id = ?
            LIMIT 1
            """
        )
        query.addBindValue(adjustment_id)

        if query.exec() and query.next():
            return [
                ("Adjustment ID", query.value(0)),
                ("Date", query.value(1)),
                ("Type", query.value(2)),
                ("Qty Change", query.value(3)),
                ("Old Qty", query.value(4)),
                ("New Qty", query.value(5)),
                ("Reason", query.value(6)),
                ("Adjusted By", query.value(7)),
                ("Batch", query.value(8)),
            ]

        return None

    def get_purchase_item_reference_details(self, purchase_item_id):
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                pi.id,
                pi.creation_date,
                COALESCE(p.display_name, ''),
                COALESCE(pi.qty, 0),
                COALESCE(pi.rate, 0),
                COALESCE(pi.total, 0)
            FROM purchaseitem pi
            LEFT JOIN product p ON p.id = pi.product
            WHERE pi.id = ?
            LIMIT 1
            """
        )
        query.addBindValue(purchase_item_id)

        if query.exec() and query.next():
            return [
                ("Purchase Item ID", query.value(0)),
                ("Date", query.value(1)),
                ("Product", query.value(2)),
                ("Qty", query.value(3)),
                ("Rate", query.value(4)),
                ("Total", query.value(5)),
            ]

        return None

    def get_purchase_reference_details(self, purchase_id):
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                p.id,
                p.creation_date,
                COALESCE(s.name, ''),
                COALESCE(r.name, ''),
                COALESCE(p.sellerinvoice, ''),
                COALESCE(p.total, 0),
                COALESCE(p.paid, 0),
                COALESCE(p.remaining, 0)
            FROM purchase p
            LEFT JOIN supplier s ON s.id = p.supplier
            LEFT JOIN rep r ON r.id = p.rep
            WHERE p.id = ?
            LIMIT 1
            """
        )
        query.addBindValue(purchase_id)

        if query.exec() and query.next():
            return [
                ("Purchase ID", query.value(0)),
                ("Date", query.value(1)),
                ("Supplier", query.value(2)),
                ("Rep", query.value(3)),
                ("Seller Invoice", query.value(4)),
                ("Total", query.value(5)),
                ("Paid", query.value(6)),
                ("Remaining", query.value(7)),
            ]

        return None

    def get_po_reference_details(self, po_id):
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                po.id,
                COALESCE(po.po_number, ''),
                COALESCE(po.po_date, ''),
                COALESCE(s.name, ''),
                COALESCE(po.status, ''),
                COALESCE(po.total_value, 0),
                COALESCE(po.expected_delivery_date, ''),
                COALESCE((SELECT SUM(qty_ordered) FROM purchase_order_line WHERE po_id = po.id), 0),
                COALESCE((
                    SELECT SUM(grl.qty_received)
                    FROM goods_receipt_line grl
                    JOIN purchase_order_line pol ON pol.id = grl.po_line_id
                    WHERE pol.po_id = po.id
                ), 0)
            FROM purchase_order po
            LEFT JOIN supplier s ON s.id = po.supplier
            WHERE po.id = ?
            LIMIT 1
            """
        )
        query.addBindValue(po_id)

        if query.exec() and query.next():
            ordered_qty = float(query.value(7) or 0)
            received_qty = float(query.value(8) or 0)
            return [
                ("PO ID", query.value(0)),
                ("PO Number", query.value(1)),
                ("PO Date", query.value(2)),
                ("Supplier", query.value(3)),
                ("Status", query.value(4)),
                ("Total Value", query.value(5)),
                ("Expected Delivery", query.value(6)),
                ("Ordered Qty", query.value(7)),
                ("Received Qty", query.value(8)),
                ("Remaining Qty", max(ordered_qty - received_qty, 0.0)),
            ]

        return None

    def get_grn_reference_details(self, grn_id):
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                gr.id,
                COALESCE(gr.grn_number, ''),
                COALESCE(gr.grn_date, ''),
                COALESCE(po.po_number, ''),
                COALESCE(s.name, ''),
                COALESCE(gr.status, ''),
                COALESCE(gr.total_value, 0)
            FROM goods_receipt gr
            LEFT JOIN purchase_order po ON po.id = gr.po_id
            LEFT JOIN supplier s ON s.id = po.supplier
            WHERE gr.id = ?
            LIMIT 1
            """
        )
        query.addBindValue(grn_id)

        if query.exec() and query.next():
            return [
                ("GRN ID", query.value(0)),
                ("GRN Number", query.value(1)),
                ("GRN Date", query.value(2)),
                ("PO Number", query.value(3)),
                ("Supplier", query.value(4)),
                ("Status", query.value(5)),
                ("Total Value", query.value(6)),
            ]

        return None

    def get_customer_transaction_reference_details(self, txn_id):
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                ct.id,
                ct.creation_date,
                COALESCE(c.name, ''),
                COALESCE(ct.transaction_type, ''),
                COALESCE(ct.ref, 0),
                COALESCE(ct.received, 0),
                COALESCE(ct.payment_method, ''),
                COALESCE(ct.payment_reference, '')
            FROM customer_transaction ct
            LEFT JOIN customer c ON c.id = ct.customer
            WHERE ct.id = ?
            LIMIT 1
            """
        )
        query.addBindValue(txn_id)

        if query.exec() and query.next():
            return [
                ("Receipt ID", query.value(0)),
                ("Date", query.value(1)),
                ("Customer", query.value(2)),
                ("Transaction Type", query.value(3)),
                ("Reference", query.value(4)),
                ("Amount Received", query.value(5)),
                ("Payment Method", query.value(6)),
                ("Payment Reference", query.value(7)),
            ]

        return None

    def get_price_change_reference_details(self, change_id):
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                pc.id,
                pc.created_at,
                COALESCE(p.display_name, ''),
                COALESCE(pc.previous_price, 0),
                COALESCE(pc.new_price, 0),
                COALESCE(pc.source, ''),
                COALESCE(pc.username, '')
            FROM price_changes pc
            LEFT JOIN product p ON p.id = pc.product_id
            WHERE pc.id = ?
            LIMIT 1
            """
        )
        query.addBindValue(change_id)

        if query.exec() and query.next():
            return [
                ("Change ID", query.value(0)),
                ("Date", query.value(1)),
                ("Product", query.value(2)),
                ("Previous Price", query.value(3)),
                ("New Price", query.value(4)),
                ("Source", query.value(5)),
                ("Username", query.value(6)),
            ]

        return None

    def get_daily_session_reference_details(self, session_id):
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                id,
                COALESCE(session_date, ''),
                COALESCE(opening_cash, 0),
                COALESCE(system_cash, 0),
                COALESCE(actual_cash, 0),
                COALESCE(withdrawal, 0),
                COALESCE(cash_difference, 0),
                COALESCE(opened_at, ''),
                COALESCE(closed_at, ''),
                COALESCE(status, '')
            FROM daily_session
            WHERE id = ?
            LIMIT 1
            """
        )
        query.addBindValue(session_id)

        if query.exec() and query.next():
            return [
                ("Session ID", query.value(0)),
                ("Session Date", query.value(1)),
                ("Opening Cash", query.value(2)),
                ("System Cash", query.value(3)),
                ("Actual Cash", query.value(4)),
                ("Withdrawal", query.value(5)),
                ("Cash Difference", query.value(6)),
                ("Opened At", query.value(7)),
                ("Closed At", query.value(8)),
                ("Status", query.value(9)),
            ]

        return None

    def get_opening_stock_cost_review_rows(self):
        query = QSqlQuery()
        if not query.exec(
            """
            WITH sold_rollup AS (
                SELECT
                    sb.batch_id,
                    COALESCE(SUM(sb.qty_taken), 0) AS sold_qty,
                    COALESCE(SUM(CASE WHEN sb.unit_cost IS NULL THEN sb.qty_taken ELSE 0 END), 0) AS unknown_sold_qty
                FROM sold_batch sb
                GROUP BY sb.batch_id
            )
            SELECT
                b.id,
                COALESCE(p.display_name, ''),
                COALESCE(b.batch_no, ''),
                COALESCE(b.expiry_date, ''),
                COALESCE(b.total_received, 0),
                COALESCE(b.quantity_remaining, 0),
                COALESCE(sr.sold_qty, 0),
                COALESCE(sr.unknown_sold_qty, 0),
                b.unit_cost,
                COALESCE(b.received_at, '')
            FROM batch b
            JOIN product p ON p.id = b.product_id
            LEFT JOIN sold_rollup sr ON sr.batch_id = b.id
            WHERE LOWER(COALESCE(b.source, '')) = 'opening'
            ORDER BY
                CASE WHEN b.unit_cost IS NULL THEN 0 ELSE 1 END,
                p.display_name ASC,
                b.received_at ASC,
                b.id ASC
            """
        ):
            raise Exception(f"Could not load opening stock batches: {query.lastError().text()}")

        rows = []
        while query.next():
            unit_cost_value = query.value(8)
            rows.append(
                {
                    "batch_id": int(query.value(0) or 0),
                    "product_name": str(query.value(1) or ""),
                    "batch_no": str(query.value(2) or ""),
                    "expiry_date": str(query.value(3) or ""),
                    "added_qty": self._to_float(query.value(4), 0.0),
                    "remaining_qty": self._to_float(query.value(5), 0.0),
                    "sold_qty": self._to_float(query.value(6), 0.0),
                    "unknown_sold_qty": self._to_float(query.value(7), 0.0),
                    "unit_cost": self._to_optional_float(unit_cost_value),
                    "received_at": str(query.value(9) or ""),
                }
            )
        return rows

    def save_opening_stock_cost_updates(self, updates):
        updates = list(updates or [])
        if not updates:
            return {"updated_batches": 0, "updated_sold_rows": 0}

        tx = QSqlQuery()
        if not tx.exec("BEGIN IMMEDIATE"):
            raise Exception(f"Could not start save transaction: {tx.lastError().text()}")

        try:
            updated_batches = 0
            updated_sold_rows = 0

            for batch_id, new_cost in updates:
                batch_update = QSqlQuery()
                batch_update.prepare("UPDATE batch SET unit_cost = ? WHERE id = ?")
                batch_update.addBindValue(new_cost)
                batch_update.addBindValue(batch_id)
                if not batch_update.exec():
                    raise Exception(batch_update.lastError().text())
                updated_batches += 1

                sold_count_query = QSqlQuery()
                sold_count_query.prepare("SELECT COUNT(*) FROM sold_batch WHERE batch_id = ?")
                sold_count_query.addBindValue(batch_id)
                sold_rows_for_batch = 0
                if sold_count_query.exec() and sold_count_query.next():
                    sold_rows_for_batch = int(sold_count_query.value(0) or 0)

                sold_update = QSqlQuery()
                sold_update.prepare(
                    """
                    UPDATE sold_batch
                    SET unit_cost = ?,
                        line_cost = ROUND(COALESCE(qty_taken, 0) * ?, 2)
                    WHERE batch_id = ?
                    """
                )
                sold_update.addBindValue(new_cost)
                sold_update.addBindValue(new_cost)
                sold_update.addBindValue(batch_id)
                if not sold_update.exec():
                    raise Exception(sold_update.lastError().text())
                updated_sold_rows += sold_rows_for_batch

            commit_query = QSqlQuery()
            if not commit_query.exec("COMMIT"):
                raise Exception(commit_query.lastError().text())

            return {
                "updated_batches": updated_batches,
                "updated_sold_rows": updated_sold_rows,
            }
        except Exception:
            rollback_query = QSqlQuery()
            rollback_query.exec("ROLLBACK")
            raise

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
        return load_opening_inventory_value()
        
        
        
        
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

    def get_near_expiry_rows(self, days=60):
        try:
            days = int(days)
        except Exception:
            days = 60
        days = max(days, 1)

        query = QSqlQuery()
        sql = f"""
            WITH parsed AS (
                SELECT
                    p.display_name,
                    b.batch_no,
                    b.expiry_date,
                    b.quantity_remaining,
                    CASE
                        WHEN b.expiry_date LIKE '____-__-__' THEN date(b.expiry_date)
                        WHEN b.expiry_date LIKE '__-__-____'
                            THEN date(substr(b.expiry_date, 7, 4) || '-' || substr(b.expiry_date, 4, 2) || '-' || substr(b.expiry_date, 1, 2))
                        ELSE NULL
                    END AS expiry_norm
                FROM batch b
                JOIN product p ON p.id = b.product_id
                WHERE
                    b.quantity_remaining > 0
                    AND p.status = 'used'
                    AND b.expiry_date IS NOT NULL
            )
            SELECT
                display_name,
                batch_no,
                expiry_date,
                CAST(julianday(expiry_norm) - julianday('now') AS INTEGER) AS days_left,
                quantity_remaining
            FROM parsed
            WHERE
                expiry_norm IS NOT NULL
                AND expiry_norm <= DATE('now', '+{days} days')
            ORDER BY expiry_norm ASC
        """
        if not query.exec(sql):
            raise Exception(f"Near expiry query failed: {query.lastError().text()}")

        rows = []
        while query.next():
            rows.append(
                {
                    "product_name": query.value(0),
                    "batch_no": query.value(1),
                    "expiry_date": query.value(2),
                    "days_left": query.value(3),
                    "qty_remaining": query.value(4),
                }
            )
        return rows

    def get_low_stock_rows(self):
        query = QSqlQuery()
        sql = """
            SELECT 
                p.display_name,
                IFNULL(SUM(b.quantity_remaining), 0) AS total_stock
            FROM product p
            LEFT JOIN batch b ON b.product_id = p.id
            LEFT JOIN (
                SELECT product_id, MAX(COALESCE(reorder_level, 0)) AS reorder_level
                FROM price_pack
                GROUP BY product_id
            ) pp ON pp.product_id = p.id
            WHERE p.status = 'used'
            GROUP BY p.id
            HAVING IFNULL(SUM(b.quantity_remaining), 0) <= MAX(COALESCE(pp.reorder_level, 0))
            ORDER BY p.display_name ASC
        """
        if not query.exec(sql):
            raise Exception(f"Low stock query failed: {query.lastError().text()}")

        rows = []
        while query.next():
            rows.append(
                {
                    "product_name": query.value(0),
                    "total_stock": query.value(1),
                }
            )
        return rows
        
           
        
        
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
        
        
        
