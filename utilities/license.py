import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
)

from utilities.app_messagebox import AppMessageBox
from utilities.license_core import (
    LICENSE_PATH,
    LicenseError,
    get_machine_id_short,
    get_machine_request_payload,
    load_and_validate_saved_license,
    parse_license_text,
    save_license_text,
    validate_license_document,
)


class LicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Activation Required")
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(560)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)

        self.info_label = QLabel(
            "This machine is not activated yet.\n"
            "Send the Machine ID to the vendor, then paste or import the license file you receive."
        )
        self.info_label.setWordWrap(True)
        self.layout.addWidget(self.info_label)

        self.machine_id_input = QLineEdit(get_machine_id_short())
        self.machine_id_input.setReadOnly(True)
        self.machine_id_input.setStyleSheet("font-family: monospace; font-weight: 700;")

        machine_row = QHBoxLayout()
        machine_label = QLabel("Machine ID")
        copy_button = QPushButton("Copy")
        copy_button.clicked.connect(self.copy_machine_request)
        machine_row.addWidget(machine_label)
        machine_row.addWidget(self.machine_id_input, 1)
        machine_row.addWidget(copy_button)
        self.layout.addLayout(machine_row)

        self.request_box = QPlainTextEdit()
        self.request_box.setReadOnly(True)
        self.request_box.setPlainText(json.dumps(get_machine_request_payload(), indent=2))
        self.request_box.setPlaceholderText("Machine request details")
        self.request_box.setMaximumHeight(140)
        self.layout.addWidget(self.request_box)

        self.license_input = QPlainTextEdit()
        self.license_input.setPlaceholderText("Paste the full license JSON here")
        self.license_input.setMinimumHeight(180)
        self.layout.addWidget(self.license_input)

        button_row = QHBoxLayout()
        import_button = QPushButton("Import License File")
        import_button.clicked.connect(self.import_license_file)
        activate_button = QPushButton("Activate")
        activate_button.clicked.connect(self.activate_license)
        button_row.addWidget(import_button)
        button_row.addStretch(1)
        button_row.addWidget(activate_button)
        self.layout.addLayout(button_row)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.layout.addWidget(self.status_label)

        startup_result = load_and_validate_saved_license()
        if not startup_result.valid:
            self.status_label.setText(startup_result.reason)
        else:
            self.status_label.setText("A valid license is already installed.")

    def copy_machine_request(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.request_box.toPlainText())
        self.status_label.setText("Machine request details copied to clipboard.")

    def import_license_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select License File",
            str(Path.home()),
            "License Files (*.dat *.json);;All Files (*)",
        )
        if not path:
            return
        try:
            raw_text = Path(path).read_text(encoding="utf-8")
        except Exception as exc:
            AppMessageBox.critical(self, "Error", f"Unable to read license file:\n{exc}")
            return

        self.license_input.setPlainText(raw_text)
        self.status_label.setText(f"Loaded license file from {path}")

    def activate_license(self):
        raw_text = self.license_input.toPlainText().strip()
        if not raw_text:
            AppMessageBox.warning(self, "No License", "Paste or import a license file first.")
            return

        try:
            document = parse_license_text(raw_text)
        except LicenseError as exc:
            AppMessageBox.warning(self, "Invalid License", str(exc))
            return

        result = validate_license_document(document)
        self.status_label.setText(result.reason)
        if not result.valid:
            AppMessageBox.warning(self, "Activation Failed", result.reason)
            return

        save_license_text(raw_text)
        AppMessageBox.information(
            self,
            "Activation Successful",
            f"License saved to:\n{LICENSE_PATH}",
        )
        self.accept()


def ensure_valid_license(parent=None) -> bool:
    result = load_and_validate_saved_license()
    if result.valid:
        return True

    dialog = LicenseDialog(parent=parent)
    return dialog.exec() == QDialog.Accepted

