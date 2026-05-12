"""Modern Date Picker Widget for PySide6 with explicit styling."""

from datetime import datetime
from PySide6.QtCore import Qt, QDate, Signal, QSize, QRect
from PySide6.QtGui import QColor, QFont, QPainter, QBrush, QPen
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QCalendarWidget, QLabel, QWidget,
    QDateEdit, QSpinBox, QToolButton, QMenu, QAbstractSpinBox, QTableView
)


class ModernDatePickerDialog(QDialog):
    """Modern popup date picker dialog with explicit color scheme."""
    
    date_selected = Signal(QDate)
    
    # Color scheme - matching ProCure theme
    COLORS = {
        "primary_dark": "#163B5C",      # Dark blue
        "primary_main": "#2F5D7C",      # Main blue
        "primary_light": "#5A8FB5",     # Light blue
        "primary_lighter": "#8FBFE4",   # Lighter blue
        "accent": "#3E87B6",            # Accent blue
        "success": "#2E7D5A",           # Green for confirmation
        "text_primary": "#222222",      # Dark text
        "text_secondary": "#666666",    # Secondary text
        "bg_primary": "#FFFFFF",        # White background
        "bg_secondary": "#F9FCFE",      # Very light blue
        "bg_tertiary": "#EEF5FA",       # Soft blue
        "border": "#D0DFE9",            # Light border
        "border_light": "#E8F1F8",      # Very light border
        "hover": "#EEF5FA",             # Hover background
        "header_surface": "#E7EFF5",    # Compact header/footer surface
    }
    
    def __init__(self, initial_date=None, parent=None):
        """
        Initialize modern date picker.
        
        Args:
            initial_date: QDate or datetime to set initial selection
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Select Date")
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # Set dialog size
        self.setFixedSize(376, 382)
        
        # Initialize layout
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Calendar widget must exist before header label initialization.
        self.calendar = self._create_calendar()

        # Header
        header = self._create_header()
        layout.addLayout(header)

        # Calendar widget
        layout.addWidget(self.calendar)
        
        # Footer with buttons
        footer = self._create_footer()
        layout.addLayout(footer)
        
        self.setLayout(layout)
        self._apply_stylesheet()
        
        # Set initial date
        if initial_date:
            if isinstance(initial_date, datetime):
                initial_date = QDate(initial_date.year, initial_date.month, initial_date.day)
            self.calendar.setSelectedDate(initial_date)
        else:
            self.calendar.setSelectedDate(QDate.currentDate())
    
    def _create_header(self):
        """Create header with date display and close button."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        self.date_label = QLabel()
        self.date_label.setFont(QFont("Montserrat", 12, QFont.Bold))
        self.date_label.setStyleSheet(
            f"color: {self.COLORS['primary_dark']}; padding: 7px 9px; "
            f"background-color: {self.COLORS['header_surface']}; border-radius: 6px;"
        )
        self._update_date_label()
        
        layout.addWidget(self.date_label)
        layout.addStretch()
        
        return layout
    
    def _create_calendar(self):
        """Create styled calendar widget."""
        calendar = QCalendarWidget()
        calendar.setFirstDayOfWeek(Qt.Monday)
        calendar.setGridVisible(False)
        calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        
        # Set initial date
        calendar.setSelectedDate(QDate.currentDate())
        
        # Connect date change signal
        calendar.clicked.connect(self._on_date_selected)
        calendar.selectionChanged.connect(self._on_selection_changed)
        
        # Apply stylesheet
        self._apply_calendar_stylesheet(calendar)
        self._configure_calendar_navigation(calendar)
        
        return calendar

    def _configure_calendar_navigation(self, calendar):
        """Tighten month/year navigation behavior after calendar creation."""
        calendar.currentPageChanged.connect(self._sync_calendar_navigation)

        calendar_view = calendar.findChild(QTableView, "qt_calendar_calendarview")
        if calendar_view is not None:
            calendar_view.horizontalHeader().setDefaultSectionSize(34)
            calendar_view.verticalHeader().setDefaultSectionSize(24)
            calendar_view.horizontalHeader().setMinimumSectionSize(34)
            calendar_view.verticalHeader().setMinimumSectionSize(24)

        month_button = calendar.findChild(QToolButton, "qt_calendar_monthbutton")
        if month_button is not None:
            month_button.setMinimumWidth(124)
            month_button.setMaximumWidth(124)
            month_menu = month_button.menu()
            if month_menu is not None:
                month_menu.setStyleSheet(f"""
                    QMenu {{
                        background-color: {self.COLORS['bg_primary']};
                        color: {self.COLORS['text_primary']};
                        border: 1px solid {self.COLORS['border']};
                        padding: 4px;
                    }}
                    QMenu::item {{
                        color: {self.COLORS['text_primary']};
                        padding: 6px 18px;
                        border-radius: 4px;
                    }}
                    QMenu::item:selected {{
                        background-color: {self.COLORS['hover']};
                        color: {self.COLORS['primary_dark']};
                    }}
                """)

        year_button = calendar.findChild(QToolButton, "qt_calendar_yearbutton")
        if year_button is not None:
            year_button.setMinimumWidth(70)
            year_button.setMaximumWidth(70)
            year_button.setPopupMode(QToolButton.InstantPopup)
            year_button.setText(str(calendar.yearShown()))
            year_menu = QMenu(year_button)
            year_menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {self.COLORS['bg_primary']};
                    color: {self.COLORS['text_primary']};
                    border: 1px solid {self.COLORS['border']};
                    padding: 4px;
                }}
                QMenu::item {{
                    color: {self.COLORS['text_primary']};
                    padding: 6px 18px;
                    border-radius: 4px;
                }}
                QMenu::item:selected {{
                    background-color: {self.COLORS['hover']};
                    color: {self.COLORS['primary_dark']};
                }}
            """)
            current_year = QDate.currentDate().year()
            for year in range(current_year, current_year + 10):
                action = year_menu.addAction(str(year))
                action.triggered.connect(
                    lambda checked=False, y=year: self._set_calendar_year(y)
                )
            year_button.setMenu(year_menu)

        year_edit = calendar.findChild(QSpinBox, "qt_calendar_yearedit")
        if year_edit is not None:
            year_edit.hide()

    def _sync_calendar_navigation(self, year, month):
        _ = month
        year_button = self.calendar.findChild(QToolButton, "qt_calendar_yearbutton")
        if year_button is not None:
            year_button.setText(str(year))

    def _set_calendar_year(self, year):
        current_month = self.calendar.monthShown()
        current_selected = self.calendar.selectedDate()
        day = min(current_selected.day(), QDate(year, current_month, 1).daysInMonth())
        self.calendar.setCurrentPage(year, current_month)
        self.calendar.setSelectedDate(QDate(year, current_month, day))
        self._update_date_label()
    
    def _apply_calendar_stylesheet(self, calendar):
        """Apply explicit styling to calendar widget."""
        stylesheet = f"""
            QCalendarWidget {{
                background-color: {self.COLORS['bg_primary']};
                border: 1px solid {self.COLORS['border']};
                border-radius: 8px;
            }}
            
            QCalendarWidget QWidget {{
                alternate-background-color: {self.COLORS['bg_primary']};
                background-color: {self.COLORS['bg_primary']};
            }}
            
            /* Header with month/year navigation */
            QCalendarWidget QToolButton {{
                background-color: {self.COLORS['primary_main']};
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 2px 7px;
                min-height: 22px;
                font-size: 10px;
                font-family: 'Montserrat';
            }}
            
            QCalendarWidget QToolButton::hover {{
                background-color: {self.COLORS['primary_light']};
            }}
            
            QCalendarWidget QToolButton::pressed {{
                background-color: {self.COLORS['primary_dark']};
            }}
            
            QCalendarWidget QToolButton#qt_calendar_prevmonth {{
                width: 28px;
            }}
            
            QCalendarWidget QToolButton#qt_calendar_nextmonth {{
                width: 28px;
            }}
            
            QCalendarWidget QToolButton#qt_calendar_monthbutton {{
                min-width: 124px;
                max-width: 124px;
            }}
            
            QCalendarWidget QToolButton#qt_calendar_yearbutton {{
                min-width: 70px;
                max-width: 70px;
            }}

            QCalendarWidget QMenu {{
                background-color: {self.COLORS['bg_primary']};
                color: {self.COLORS['text_primary']};
                border: 1px solid {self.COLORS['border']};
            }}

            QCalendarWidget QMenu::item {{
                color: {self.COLORS['text_primary']};
                padding: 6px 18px;
            }}

            QCalendarWidget QMenu::item:selected {{
                background-color: {self.COLORS['hover']};
                color: {self.COLORS['primary_dark']};
            }}

            /* Day names header */
            QCalendarWidget QAbstractItemView {{
                background-color: {self.COLORS['bg_primary']};
                border: none;
            }}
            
            QCalendarWidget QAbstractItemView:enabled {{
                color: {self.COLORS['text_primary']};
                selection-background-color: {self.COLORS['primary_main']};
            }}
            
            QCalendarWidget QAbstractItemView:disabled {{
                color: #cccccc;
            }}
            
            /* Day names styling */
            QCalendarWidget QHeaderView::section {{
                background-color: {self.COLORS['bg_secondary']};
                color: {self.COLORS['primary_dark']};
                padding: 3px;
                border: none;
                border-bottom: 1px solid {self.COLORS['border_light']};
                font-weight: bold;
                font-family: 'Montserrat';
                font-size: 9px;
            }}
            
            /* Day cells */
            QCalendarWidget QAbstractItemView::item {{
                padding: 1px;
                border: 1px solid transparent;
                margin: 0px;
            }}
            
            QCalendarWidget QAbstractItemView::item:hover {{
                background-color: {self.COLORS['hover']};
                border: 1px solid {self.COLORS['primary_lighter']};
            }}
            
            QCalendarWidget QAbstractItemView::item:selected {{
                background-color: {self.COLORS['primary_main']};
                color: white;
                border: 1px solid {self.COLORS['primary_dark']};
                font-weight: bold;
            }}
            
            QCalendarWidget QAbstractItemView::item:disabled {{
                color: #d0d0d0;
            }}
        """
        calendar.setStyleSheet(stylesheet)
    
    def _create_footer(self):
        """Create footer with action buttons."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setFixedHeight(32)
        cancel_btn.setFont(QFont("Montserrat", 10, QFont.Medium))
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.COLORS['header_surface']};
                color: {self.COLORS['text_primary']};
                border: 1px solid {self.COLORS['border']};
                border-radius: 6px;
                padding: 5px 14px;
                font-weight: 600;
                font-family: 'Montserrat';
            }}
            
            QPushButton:hover {{
                background-color: {self.COLORS['border_light']};
                border: 1px solid {self.COLORS['primary_light']};
            }}
            
            QPushButton:pressed {{
                background-color: {self.COLORS['hover']};
            }}
        """)
        
        # Confirm button
        confirm_btn = QPushButton("Confirm")
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.clicked.connect(self._confirm_selection)
        confirm_btn.setFixedHeight(32)
        confirm_btn.setFont(QFont("Montserrat", 10, QFont.Bold))
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.COLORS['primary_main']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 5px 16px;
                font-weight: 700;
                font-family: 'Montserrat';
            }}
            
            QPushButton:hover {{
                background-color: {self.COLORS['primary_light']};
            }}
            
            QPushButton:pressed {{
                background-color: {self.COLORS['primary_dark']};
            }}
        """)
        
        layout.addWidget(cancel_btn)
        layout.addWidget(confirm_btn)
        
        return layout
    
    def _apply_stylesheet(self):
        """Apply main dialog stylesheet."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.COLORS['bg_primary']};
                border: 1px solid {self.COLORS['border']};
                border-radius: 10px;
            }}
        """)
    
    def _update_date_label(self):
        """Update date label with currently selected date."""
        selected_date = self.calendar.selectedDate()
        date_str = selected_date.toString("dddd, MMMM d, yyyy")
        self.date_label.setText(date_str)
    
    def _on_date_selected(self):
        """Handle date selection in calendar."""
        self._update_date_label()
    
    def _on_selection_changed(self):
        """Handle selection change in calendar."""
        self._update_date_label()
    
    def _confirm_selection(self):
        """Confirm and close dialog."""
        selected_date = self.calendar.selectedDate()
        self.date_selected.emit(selected_date)
        self.accept()
    
    def get_selected_date(self):
        """Get the selected date."""
        return self.calendar.selectedDate()


class ModernDateEdit(QDateEdit):
    """Custom QDateEdit that uses modern date picker dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDate(QDate.currentDate())
        self.setCalendarPopup(True)
        
        # Create custom calendar widget
        self.custom_calendar = QCalendarWidget()
        self._style_calendar()
        self.setCalendarWidget(self.custom_calendar)
    
    def _style_calendar(self):
        """Style the embedded calendar widget."""
        colors = ModernDatePickerDialog.COLORS
        self.custom_calendar.setGridVisible(False)
        self.custom_calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        
        stylesheet = f"""
            QCalendarWidget {{
                background-color: {colors['bg_primary']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                gridline-color: transparent;
            }}
            
            QCalendarWidget QToolButton {{
                background-color: {colors['primary_main']};
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 3px 8px;
                margin: 1px;
                min-width: 26px;
                min-height: 24px;
                font-size: 11px;
            }}
            
            QCalendarWidget QToolButton::hover {{
                background-color: {colors['primary_light']};
            }}
            
            QCalendarWidget QToolButton::pressed {{
                background-color: {colors['primary_dark']};
            }}
            
            QCalendarWidget QMenu {{
                background-color: {colors['bg_secondary']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
            }}

            QCalendarWidget QMenu::item {{
                color: {colors['text_primary']};
                padding: 6px 18px;
            }}

            QCalendarWidget QMenu::item:selected {{
                background-color: {colors['hover']};
                color: {colors['primary_dark']};
            }}
            
            QCalendarWidget QSpinBox {{
                background-color: {colors['bg_tertiary']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                min-height: 24px;
            }}
            
            QCalendarWidget QAbstractItemView:enabled {{
                color: {colors['text_primary']};
                background-color: {colors['bg_primary']};
                selection-background-color: {colors['primary_main']};
                border-radius: 4px;
                outline: 0;
            }}
            
            QCalendarWidget QAbstractItemView:enabled:hover {{
                background-color: {colors['hover']};
            }}
            
            QCalendarWidget QAbstractItemView::item:selected {{
                color: white;
                background-color: {colors['primary_main']};
                font-weight: bold;
            }}
            
            QCalendarWidget QHeaderView {{
                background-color: {colors['bg_secondary']};
                font-weight: bold;
            }}
            
            QCalendarWidget QHeaderView::section {{
                background-color: {colors['bg_secondary']};
                color: {colors['text_primary']};
                padding: 4px;
                border: none;
                border-bottom: 1px solid {colors['border_light']};
                font-weight: bold;
                font-size: 10px;
            }}
        """
        self.custom_calendar.setStyleSheet(stylesheet)


def demo():
    """Demo application showing the modern date picker."""
    app = QApplication([])
    
    # Main window
    main_widget = QWidget()
    layout = QVBoxLayout(main_widget)
    layout.setSpacing(20)
    layout.setContentsMargins(30, 30, 30, 30)
    
    main_widget.setStyle("Fusion")
    main_widget.setStyleSheet(f"""
        QWidget {{
            background-color: #F9FCFE;
        }}
        QLabel {{
            color: #222;
            font-family: 'Montserrat';
            font-size: 14px;
        }}
    """)
    
    main_widget.setWindowTitle("Modern Date Picker Demo")
    main_widget.setGeometry(100, 100, 600, 400)
    
    # Title
    title = QLabel("Modern Date Picker Components")
    title.setFont(QFont("Montserrat", 18, QFont.Bold))
    title.setStyleSheet("color: #2F5D7C;")
    layout.addWidget(title)
    
    # Dialog button
    dialog_btn = QPushButton("Open Date Picker Dialog")
    dialog_btn.setFixedHeight(45)
    dialog_btn.setFont(QFont("Montserrat", 12, QFont.Bold))
    dialog_btn.setStyleSheet("""
        QPushButton {
            background-color: #2F5D7C;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #5A8FB5;
        }
        QPushButton:pressed {
            background-color: #163B5C;
        }
    """)
    
    selected_date_label = QLabel("Selected: None")
    selected_date_label.setStyleSheet("color: #2F5D7C; font-weight: bold; font-size: 14px;")
    
    def open_picker():
        picker = ModernDatePickerDialog()
        if picker.exec() == QDialog.Accepted:
            date = picker.get_selected_date()
            selected_date_label.setText(f"Selected: {date.toString('dddd, MMMM d, yyyy')}")
    
    dialog_btn.clicked.connect(open_picker)
    layout.addWidget(dialog_btn)
    layout.addWidget(selected_date_label)
    
    # Embedded calendar in QDateEdit
    edit_label = QLabel("Modern Date Edit (embedded calendar):")
    edit_label.setFont(QFont("Montserrat", 12, QFont.Bold))
    layout.addWidget(edit_label)
    
    date_edit = ModernDateEdit()
    date_edit.setFixedHeight(40)
    date_edit.setFont(QFont("Montserrat", 11))
    layout.addWidget(date_edit)
    
    layout.addStretch()
    
    main_widget.show()
    app.exec()


if __name__ == "__main__":
    demo()
