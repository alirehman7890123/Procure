from __future__ import annotations

from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QApplication
from medic.services.accounting_settings_service import load_theme_settings

DEFAULT_THEME = {
    "theme_primary_color": "#0E8B86",
    "theme_sidebar_color": "#062B35",
}
LEGACY_THEME = {
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
    raw_primary = normalize_hex(settings["theme_primary_color"], DEFAULT_THEME["theme_primary_color"])
    raw_sidebar = normalize_hex(settings["theme_sidebar_color"], DEFAULT_THEME["theme_sidebar_color"])

    # Preserve explicitly customized themes, but treat the legacy built-in
    # blue defaults as "unset" so the app can move forward to the newer teal
    # shell without requiring a manual DB theme reset.
    if raw_primary == LEGACY_THEME["theme_primary_color"]:
        raw_primary = DEFAULT_THEME["theme_primary_color"]
    if raw_sidebar == LEGACY_THEME["theme_sidebar_color"]:
        raw_sidebar = DEFAULT_THEME["theme_sidebar_color"]

    return {
        "theme_primary_color": raw_primary,
        "theme_sidebar_color": raw_sidebar,
    }


def get_theme_palette():
    settings = get_theme_settings()
    primary = settings["theme_primary_color"]
    sidebar = settings["theme_sidebar_color"]
    return {
        "primary_main": primary,
        "primary_hover": tint(primary, -0.12),
        "primary_pressed": tint(primary, -0.24),
        "primary_border": tint(primary, -0.18),
        "focus_border": tint(primary, 0.28),
        "focus_fill": tint(primary, 0.88),
        "table_soft": tint(primary, 0.92),
        "table_border": tint(primary, 0.72),
        "sidebar_bg": sidebar,
        "sidebar_border": tint(sidebar, 0.12),
        "sidebar_hover": tint(sidebar, 0.20),
        "sidebar_active": "#0D8C86",
        "sidebar_active_text": "#F5FEFD",
        "sidebar_text": "#E6F5F2",
    }


def apply_app_theme():
    app = QApplication.instance()
    if app is None:
        return

    from .stylus import load_stylesheets

    app.setFont(QFont("Inter", 12))
    stylesheet = load_stylesheets()
    app.setStyleSheet(stylesheet)

    for widget in app.topLevelWidgets():
        refresh = getattr(widget, "refresh_theme", None)
        if callable(refresh):
            try:
                refresh()
            except Exception as exc:
                print("Theme refresh failed:", str(exc))
