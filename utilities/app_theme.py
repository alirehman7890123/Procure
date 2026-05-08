from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication
from medic.services.accounting_settings_service import load_theme_settings

DEFAULT_THEME = {
    "theme_primary_color": "#163B5C",
    "theme_sidebar_color": "#163B5C",
}


def normalize_hex(value, fallback):
    text = str(value or "").strip()
    if not text:
        return fallback
    if not text.startswith("#"):
        text = f"#{text}"
    color = QColor(text)
    return color.name().upper() if color.isValid() else fallback


def tint(color_value, factor):
    color = QColor(color_value)
    if not color.isValid():
        color = QColor(DEFAULT_THEME["theme_primary_color"])

    factor = max(-1.0, min(1.0, float(factor)))
    if factor >= 0:
        return color.lighter(int(100 + factor * 100)).name().upper()
    return color.darker(int(100 + abs(factor) * 100)).name().upper()


def get_theme_settings():
    settings = load_theme_settings()
    return {
        "theme_primary_color": normalize_hex(settings["theme_primary_color"], DEFAULT_THEME["theme_primary_color"]),
        "theme_sidebar_color": normalize_hex(settings["theme_sidebar_color"], DEFAULT_THEME["theme_sidebar_color"]),
    }


def get_theme_palette():
    settings = get_theme_settings()
    primary = settings["theme_primary_color"]
    sidebar = settings["theme_sidebar_color"]
    return {
        "primary_main": primary,
        "primary_hover": tint(primary, -0.18),
        "primary_pressed": tint(primary, -0.35),
        "primary_border": tint(primary, -0.15),
        "focus_border": tint(primary, 0.28),
        "focus_fill": tint(primary, 0.88),
        "table_soft": tint(primary, 0.92),
        "table_border": tint(primary, 0.72),
        "sidebar_bg": sidebar,
        "sidebar_border": tint(sidebar, 0.18),
        "sidebar_hover": tint(sidebar, 0.22),
        "sidebar_active": tint(primary, 0.92),
        "sidebar_active_text": tint(primary, -0.65),
        "sidebar_text": "#DDD9EB",
    }


def apply_app_theme():
    app = QApplication.instance()
    if app is None:
        return

    from .stylus import load_stylesheets

    stylesheet = load_stylesheets()
    app.setStyleSheet(stylesheet)

    for widget in app.topLevelWidgets():
        refresh = getattr(widget, "refresh_theme", None)
        if callable(refresh):
            try:
                refresh()
            except Exception as exc:
                print("Theme refresh failed:", str(exc))
