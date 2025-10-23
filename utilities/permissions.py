
from functools import wraps
from PySide6.QtWidgets import QApplication, QMessageBox

class Permissions:
    
    

    
    
    @staticmethod
    def require_permission(page_name):
        """Decorator to check if the current user has access to a given page."""
        
        PERMISSIONS = {
                    # Dashboard
                    "dashboard": {"admin", "manager"},
                    
                    # Business
                    "business.view": {"admin", "manager", "regular"},
                    "business.update": {"admin"},

                    # Profile
                    "profile.view": {"admin", "manager", "regular"},
                    "profile.update": {"admin", "manager", "regular"},

                    # Users (system-level, so stricter)
                    "users.view": {"admin", "manager"},
                    "users.create": {"admin", "manager"},
                    "users.update": {"admin", "manager"},
                    "users.delete": {"admin"},

                    # Supplier
                    "supplier.view": {"admin", "manager", "regular"},
                    "supplier.create": {"admin", "manager"},
                    "supplier.update": {"admin", "manager"},
                    "supplier.delete": {"admin"},

                    # Sales Representatives
                    "rep.view": {"admin", "manager"},
                    "rep.create": {"admin", "manager"},
                    "rep.update": {"admin", "manager"},
                    "rep.delete": {"admin"},

                    # Customers
                    "customer.view": {"admin", "manager", "regular"},
                    "customer.create": {"admin", "manager", "regular"},
                    "customer.update": {"admin", "manager"},
                    "customer.delete": {"admin"},

                    # Employees
                    "employee.view": {"admin", "manager"},
                    "employee.create": {"admin", "manager"},
                    "employee.update": {"admin"},
                    "employee.delete": {"admin"},

                    # Purchases
                    "purchase.view": {"admin", "manager", "regular"},
                    "purchase.create": {"admin", "manager"},
                    "purchase.update": {"admin", "manager"},
                    "purchase.delete": {"admin"},

                    # Purchase Returns
                    "purchasereturn.view": {"admin", "manager"},
                    "purchasereturn.create": {"admin"},
                    "purchasereturn.update": {"admin"},
                    "purchasereturn.delete": {"admin"},

                    # Sales
                    "sales.view": {"admin", "manager", "regular"},
                    "sales.create": {"admin", "manager", "regular"},
                    "sales.update": {"admin", "manager"},
                    "sales.delete": {"admin"},

                    # Sales Returns
                    "salesreturn.view": {"admin", "manager", "regular"},
                    "salesreturn.create": {"admin", "manager", "regular"},
                    "salesreturn.update": {"admin", "manager"},
                    "salesreturn.delete": {"admin"},

                    # Transactions (financial, very restricted)
                    "transactions.view": {"admin", "manager"},
                    "transactions.create": {"admin", "manager"},
                    "transactions.update": {"admin", "manager"},
                    "transactions.delete": {"admin"},

                    # Reports
                    "reports.view": {"admin", "manager"},
                }
        
        
        def decorator(func):
            @wraps(func)
            def wrapper(obj, *args, **kwargs):  # use obj instead of self to avoid confusion
                role = QApplication.instance().property("user_role")
                allowed_roles = PERMISSIONS.get(page_name, set())

                if role not in allowed_roles:
                    QMessageBox.critical(
                        obj,
                        "Not Authorized",
                        f"Your role '{role}' does not have permission to access '{page_name}'."
                    )
                    return None  # explicit return
                
                return func(obj, *args, **kwargs)
            
            return wrapper
        
        return decorator



