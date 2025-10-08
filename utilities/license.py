# gimmick_license.py
import sys
import os
import uuid
import hashlib
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QMainWindow
)
from PySide6.QtCore import Qt, QTimer

LICENSE_FILE = os.path.expanduser("~/.myapp_license_key")  # simple local store


def get_machine_id_short():
    mac = uuid.getnode()
    # short readable id (not secure) — just for show
    return hashlib.sha1(str(mac).encode()).hexdigest()[:12].upper()


def save_license(key: str):
    try:
        with open(LICENSE_FILE, "w") as f:
            f.write(key)
    except Exception:
        pass


def load_saved_license():
    try:
        if os.path.exists(LICENSE_FILE):
            with open(LICENSE_FILE, "r") as f:
                return f.read().strip()
    except Exception:
        pass
    return None


class LicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Activation Required")
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedWidth(420)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self._info = QLabel(
            "This copy requires activation.\n"
            "Please enter the activation key provided to you.\n"
            "Machine ID (for activation):"
        )
        self.layout.addWidget(self._info)

        self.machine_id = QLabel(get_machine_id_short())
        self.machine_id.setStyleSheet("font-family: monospace; font-weight: bold;")
        self.layout.addWidget(self.machine_id)

        self.layout.addSpacing(6)
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Enter activation key here")
        self.layout.addWidget(self.key_input)

        self.activate_btn = QPushButton("Activate")
        self.activate_btn.clicked.connect(self._on_activate)
        self.layout.addWidget(self.activate_btn)

        self.status = QLabel("")  # status text (verifying / success / fail)
        self.layout.addWidget(self.status)

        # keep small hint to user
        self.layout.addStretch()

    def _on_activate(self):
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "No key", "Please enter a key to continue.")
            return

        # disable UI while "verifying"
        self.key_input.setEnabled(False)
        self.activate_btn.setEnabled(False)
        self.status.setText("Verifying activation key…")
        QApplication.processEvents()

        # fake network / heavy check delay (2 seconds)
        QTimer.singleShot(2000, lambda: self._finish_verify(key))

    def _finish_verify(self, key):
        # GIMMICK LOGIC: accept any non-empty key (we'll make it feel "real")
        # You can replace this with actual server or cryptographic check later.
        accepted = bool(key)

        if accepted:
            save_license(key)
            self.status.setText("Activation successful ✅")
            QTimer.singleShot(600, self.accept)  # close shortly after success
        else:
            self.status.setText("Activation failed ✖")
            self.key_input.setEnabled(True)
            self.activate_btn.setEnabled(True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App (Demo)")
        label = QLabel("App unlocked — enjoy the demo!", self)
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)
        self.resize(600, 400)


def main():
    app = QApplication(sys.argv)

    # if saved license exists, skip dialog (gimmick behavior)
    saved = load_saved_license()
    if saved:
        # optional: show a very short "verifying" toast — for realism
        # (we'll just proceed)
        pass
    else:
        dlg = LicenseDialog()
        if dlg.exec() != QDialog.Accepted:
            # user cancelled or failed — exit app
            return

    # show real main window
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
