

from functools import wraps
from PySide6.QtWidgets import QApplication, QMessageBox
from medic.utilities.app_messagebox import AppMessageBox


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

            "po.view", "po.create", "po.update", "po.delete",

            "grn.view", "grn.create", "grn.update", "grn.delete",
            "grn.audit",

            "purchasereturn.view", "purchasereturn.create", "purchasereturn.update", "purchasereturn.delete",

            "sales.view", "sales.create", "sales.update", "sales.delete",

            "salesreturn.view", "salesreturn.create", "salesreturn.update", "salesreturn.delete",

            "transactions.view", "transactions.create", "transactions.update", "transactions.delete",
            
            "expense.view", "expense.create", "expense.update", "expense.delete",

            "reports.view",

            "financialclose.view", "financialclose.close", "financialclose.reopen",

            "inventory.adjust",
            "system.backup.external",

            "payroll.view", "payroll.create", "payroll.attendance", "payroll.advance",
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

            "po.view", "po.create", "po.update",

            "grn.view", "grn.create", "grn.update",

            "purchasereturn.view",

            "sales.view", "sales.create", "sales.update",

            "salesreturn.view", "salesreturn.create", "salesreturn.update",

            "transactions.view", "transactions.create", "transactions.update",

            "expense.view", "expense.create", "expense.update", "expense.delete",            
            
            "reports.view",

            "financialclose.view", "financialclose.close",

            "payroll.view", "payroll.create", "payroll.attendance", "payroll.advance",
        },

        "accountant": {
            "dashboard",

            "profile.view", "profile.update",

            "customer.view",
            "supplier.view",
            "sales.view",
            "purchase.view",

            "transactions.view", "transactions.create", "transactions.update",
            "expense.view", "expense.create", "expense.update",

            "reports.view",

            "financialclose.view", "financialclose.close", "financialclose.reopen",

            "payroll.view",
        },

        "inventory": {
            "dashboard",

            "profile.view", "profile.update",

            "supplier.view",

            "product.view", "product.create", "product.update",

            "purchase.view", "purchase.create", "purchase.update",
            "po.view", "po.create", "po.update",
            "grn.view", "grn.create", "grn.update",

            "purchasereturn.view", "purchasereturn.create",

            "reports.view",

            "financialclose.view",
        },

        "cashier": {
            "dashboard",

            "profile.view", "profile.update",

            "customer.view", "customer.create", "customer.update",

            "sales.view", "sales.create", "sales.update",
            "salesreturn.view", "salesreturn.create", "salesreturn.view",

            "transactions.view", "transactions.create",
            "expense.view", "expense.create",
        },

        "procurement": {
            "dashboard",

            "profile.view", "profile.update",

            "supplier.view", "supplier.create", "supplier.update",

            "product.view",

            "purchase.view", "purchase.create", "purchase.update",
            "po.view", "po.create", "po.update",
            "grn.view", "grn.create", "grn.update",

            "purchasereturn.view", "purchasereturn.create",

            "reports.view",
        },

        "auditor": {
            "dashboard",

            "business.view",

            "profile.view",

            "users.view",

            "supplier.view",
            "rep.view",
            "product.view",
            "customer.view",
            "employee.view",

            "payroll.view",

            "purchase.view",
            "po.view",
            "grn.view", "grn.audit",
            "purchasereturn.view",

            "sales.view",
            "salesreturn.view",

            "transactions.view",
            "expense.view",

            "reports.view",
        },

        "regular": {
            "sales.create", "sales.view",
            "profile.view", "profile.update",
            "expense.create", "expense.view",
            "purchase.create", "purchase.view",
            "po.create", "po.view",
            "grn.create", "grn.view",
        },
    }

    ROLE_ALIASES = {
        "accounts": "accountant",
        "inventory_clerk": "inventory",
        "storekeeper": "inventory",
        "sales_clerk": "cashier",
        "procurement_officer": "procurement",
    }

    ASSIGNABLE_ROLES = [
        "manager",
        "accountant",
        "inventory",
        "cashier",
        "procurement",
        "auditor",
        "regular",
    ]

    @classmethod
    def get_role(cls):
        app = QApplication.instance()
        role = app.property("user_role") if app else None
        if role is None:
            return None
        normalized_role = str(role).strip().lower()
        return cls.ROLE_ALIASES.get(normalized_role, normalized_role)

    @classmethod
    def known_roles(cls):
        return sorted(cls.ROLE_PERMISSIONS.keys())

    @classmethod
    def assignable_roles(cls):
        return [role for role in cls.ASSIGNABLE_ROLES if role in cls.ROLE_PERMISSIONS]

    @classmethod
    def all_permissions(cls):
        all_perms = set()
        for perms in cls.ROLE_PERMISSIONS.values():
            all_perms.update(perms)
        return all_perms

    @classmethod
    def is_known_permission(cls, permission_name):
        return permission_name in cls.all_permissions()

    @classmethod
    def has_permission(cls, permission_name):
        if not cls.is_known_permission(permission_name):
            return False

        role = cls.get_role()
        allowed_permissions = cls.ROLE_PERMISSIONS.get(role, set())
        return permission_name in allowed_permissions

    @classmethod
    def require_permission(cls, permission_name):
        if not cls.is_known_permission(permission_name):
            raise ValueError(f"Unknown permission key: {permission_name}")

        def decorator(func):
            @wraps(func)
            def wrapper(obj, *args, **kwargs):
                if not cls.has_permission(permission_name):
                    role = cls.get_role()
                    parent = obj if hasattr(obj, "winId") else None
                    AppMessageBox.critical(
                        parent,
                        "Not Authorized",
                        f"Your role '{role}' does not have permission to access '{permission_name}'."
                    )
                    return None

                return func(obj, *args, **kwargs)
            return wrapper
        return decorator