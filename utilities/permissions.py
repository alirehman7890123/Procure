

from functools import wraps
from PySide6.QtWidgets import QApplication, QMessageBox


class Permissions:
    ROLE_PERMISSIONS = {
        "admin": {
            "dashboard",

            "business.view", "business.update",

            "profile.view", "profile.update",

            "users.view", "users.create", "users.update", "users.delete",

            "supplier.view", "supplier.create", "supplier.update", "supplier.delete",

            "rep.view", "rep.create", "rep.update", "rep.delete",
            
            "product.view", "product.create", "product.update", "product.delete",

            "customer.view", "customer.create", "customer.update", "customer.delete",

            "employee.view", "employee.create", "employee.update", "employee.delete",

            "purchase.view", "purchase.create", "purchase.update", "purchase.delete",

            "purchasereturn.view", "purchasereturn.create", "purchasereturn.update", "purchasereturn.delete",

            "sales.view", "sales.create", "sales.update", "sales.delete",

            "salesreturn.view", "salesreturn.create", "salesreturn.update", "salesreturn.delete",

            "transactions.view", "transactions.create", "transactions.update", "transactions.delete",
            
            "expense.view", "expense.create", "expense.update", "expense.delete",

            "reports.view",
        },

        "manager": {
            "dashboard",

            "business.view",

            "profile.view", "profile.update",

            "users.view", "users.create", "users.update",

            "supplier.view", "supplier.create", "supplier.update",

            "rep.view", "rep.create", "rep.update",
            
            "product.view", "product.create", "product.update", "product.delete",

            "customer.view", "customer.create", "customer.update",

            "employee.view", "employee.create",

            "purchase.view", "purchase.create", "purchase.update",

            "purchasereturn.view",

            "sales.view", "sales.create", "sales.update",

            "salesreturn.view", "salesreturn.create", "salesreturn.update",

            "transactions.view", "transactions.create", "transactions.update",

            "expense.view", "expense.create", "expense.update", "expense.delete",            
            
            "reports.view",
        },

        "regular": {
            "sales.create", "sales.view",
            "profile.view", "profile.update",
            "expense.create", "expense.view",
            "purchase.create", "purchase.view",
        },
    }

    @classmethod
    def get_role(cls):
        app = QApplication.instance()
        return app.property("user_role") if app else None

    @classmethod
    def has_permission(cls, permission_name):
        role = cls.get_role()
        allowed_permissions = cls.ROLE_PERMISSIONS.get(role, set())
        return permission_name in allowed_permissions

    @classmethod
    def require_permission(cls, permission_name):
        def decorator(func):
            @wraps(func)
            def wrapper(obj, *args, **kwargs):
                if not cls.has_permission(permission_name):
                    role = cls.get_role()
                    QMessageBox.critical(
                        obj,
                        "Not Authorized",
                        f"Your role '{role}' does not have permission to access '{permission_name}'."
                    )
                    return None

                return func(obj, *args, **kwargs)
            return wrapper
        return decorator