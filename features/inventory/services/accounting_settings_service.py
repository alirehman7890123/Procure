"""Inventory feature bridge for accounting settings helpers."""

try:
    from medic.services.accounting_settings_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.accounting_settings_service import *  # noqa: F403
