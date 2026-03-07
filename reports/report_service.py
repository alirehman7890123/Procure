
from PySide6.QtSql import  QSqlQuery
from PySide6.QtCore import QDate



class ReportService:


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

   
        
        
            
    # def get_detailed_revenue(self, duration="today"):
    #     """
    #     Returns:
    #     - revenue_known_cost
    #     - total_cogs
    #     - gross_profit_known
    #     - revenue_unknown_cost
    #     """

    #     query_string = """
    #         SELECT
    #             SUM(CASE WHEN sb_unknown.sale_item_id IS NULL 
    #                     THEN si.effective_line_total ELSE 0 END) AS revenue_known,

    #             SUM(sb.line_cost) AS total_cogs,

    #             SUM(CASE WHEN sb_unknown.sale_item_id IS NULL 
    #                     THEN si.effective_line_total - IFNULL(sb_known.total_cogs, 0)
    #                     ELSE 0 END) AS gross_profit_known,

    #             SUM(CASE WHEN sb_unknown.sale_item_id IS NOT NULL 
    #                     THEN si.effective_line_total ELSE 0 END) AS revenue_unknown

    #         FROM salesitem si

    #         -- Known COGS per salesitem
    #         LEFT JOIN (
    #             SELECT sale_item_id, SUM(line_cost) AS total_cogs
    #             FROM sold_batch
    #             WHERE unit_cost IS NOT NULL
    #             GROUP BY sale_item_id
    #         ) sb_known ON sb_known.sale_item_id = si.id

    #         -- Detect if any unknown-cost batch exists
    #         LEFT JOIN (
    #             SELECT DISTINCT sale_item_id
    #             FROM sold_batch
    #             WHERE unit_cost IS NULL
    #         ) sb_unknown ON sb_unknown.sale_item_id = si.id

    #         -- For total COGS sum
    #         LEFT JOIN sold_batch sb 
    #             ON sb.sale_item_id = si.id 
    #         AND sb.unit_cost IS NOT NULL

    #         WHERE si.creation_date BETWEEN ? AND ?
    #     """

    #     query = QSqlQuery()
    #     query.prepare(query_string)
    #     query.addBindValue(date_from)
    #     query.addBindValue(date_to)

    #     if query.exec() and query.next():
    #         revenue_known   = float(query.value(0) or 0.0)
    #         total_cogs      = float(query.value(1) or 0.0)
    #         gross_profit    = float(query.value(2) or 0.0)
    #         revenue_unknown = float(query.value(3) or 0.0)

    #         return revenue_known, total_cogs, gross_profit, revenue_unknown

    #     return 0.0, 0.0, 0.0, 0.0 
    
        
    
    
    def get_detailed_revenue(self, duration="today"):
        """
        Returns:
            revenue_known_cost
            total_cogs
            gross_profit_known
            revenue_unknown_cost
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
            return 0.0, 0.0, 0.0, 0.0

        query = QSqlQuery()

        sql = f"""
            SELECT
                IFNULL(SUM(CASE 
                    WHEN sb_unknown.sale_item_id IS NULL 
                    THEN si.effective_line_total 
                    ELSE 0 END), 0) AS revenue_known,

                IFNULL(SUM(sb.line_cost), 0) AS total_cogs,

                IFNULL(SUM(CASE 
                    WHEN sb_unknown.sale_item_id IS NULL 
                    THEN si.effective_line_total - IFNULL(sb_known.total_cogs, 0)
                    ELSE 0 END), 0) AS gross_profit_known,

                IFNULL(SUM(CASE 
                    WHEN sb_unknown.sale_item_id IS NOT NULL 
                    THEN si.effective_line_total 
                    ELSE 0 END), 0) AS revenue_unknown

            FROM salesitem si

            LEFT JOIN (
                SELECT sale_item_id, SUM(line_cost) AS total_cogs
                FROM sold_batch
                WHERE unit_cost IS NOT NULL
                GROUP BY sale_item_id
            ) sb_known ON sb_known.sale_item_id = si.id

            LEFT JOIN (
                SELECT DISTINCT sale_item_id
                FROM sold_batch
                WHERE unit_cost IS NULL
            ) sb_unknown ON sb_unknown.sale_item_id = si.id

            LEFT JOIN sold_batch sb 
                ON sb.sale_item_id = si.id 
                AND sb.unit_cost IS NOT NULL

            WHERE {where_clause}
        """

        if not query.exec(sql):
            print("Detailed revenue query failed:", query.lastError().text())
            return 0.0, 0.0, 0.0, 0.0

        if query.next():
            revenue_known   = float(query.value(0) or 0.0)
            total_cogs      = float(query.value(1) or 0.0)
            gross_profit    = float(query.value(2) or 0.0)
            revenue_unknown = float(query.value(3) or 0.0)

            return revenue_known, total_cogs, gross_profit, revenue_unknown

        return 0.0, 0.0, 0.0, 0.0
            
            
        
    
                
            
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
            FROM batch
            WHERE expiry_date IS NOT NULL
            AND expiry_date BETWEEN ? AND ?
            AND quantity_remaining > 0
        """

        near_expiry_batches = get_count(
            near_expiry_query,
            today.toString("yyyy-MM-dd"),
            six_months_later.toString("yyyy-MM-dd"),
        )

        # 2️⃣ Low Stock Products (total stock <= 0)
        low_stock_query = """
            SELECT COUNT(*)
            FROM (
                SELECT product_id, SUM(quantity_remaining) AS total_qty
                FROM batch
                GROUP BY product_id
                HAVING total_qty <= 0 OR total_qty IS NULL
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
        
        
        
        