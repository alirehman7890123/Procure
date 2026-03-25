from PySide6.QtSql import QSqlQuery

def get_current_session(self):
        
        query = QSqlQuery()
        query.prepare("SELECT id FROM daily_session WHERE status = 'open' LIMIT 1;")

        if not query.exec():
            print("Error fetching current session:", query.lastError().text())
            return None

        if query.next():
            return query.value(0)

        print("No active session found.")
        return None