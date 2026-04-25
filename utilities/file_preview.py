import os
import platform
import subprocess

from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QScrollArea, QLabel, QSizePolicy
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QSize

from medic.utilities.app_messagebox import AppMessageBox

try:
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView
    HAS_QT_PDF = True
except Exception:
    QPdfDocument = None
    QPdfView = None
    HAS_QT_PDF = False


class ImagePreviewDialog(QDialog):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.preview_ready = False
        self.setWindowTitle(os.path.basename(file_path) or "Image Preview")
        self.resize(900, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            image_label.setText("Could not load image preview.")
        else:
            scaled = pixmap.scaled(QSize(1200, 1200), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(scaled)
            self.preview_ready = True

        scroll.setWidget(image_label)
        layout.addWidget(scroll)

        close_btn = QPushButton("Close", objectName="TopRightButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, 0, Qt.AlignRight)


class PdfPreviewDialog(QDialog):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.preview_ready = False
        self.setWindowTitle(os.path.basename(file_path) or "PDF Preview")
        self.resize(980, 760)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.document = QPdfDocument(self)
        load_result = self.document.load(file_path)
        load_failed, failure_reason = self._load_failed(self.document, load_result)
        if load_failed:
            error_label = QLabel("Could not load PDF preview.")
            error_label.setWordWrap(True)
            layout.addWidget(error_label)
            if failure_reason:
                detail_label = QLabel(failure_reason)
                detail_label.setWordWrap(True)
                detail_label.setStyleSheet("color: #666; font-size: 11px;")
                layout.addWidget(detail_label)
        else:
            pdf_view = QPdfView()
            pdf_view.setDocument(self.document)
            pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
            layout.addWidget(pdf_view)
            self.preview_ready = True

        close_btn = QPushButton("Close", objectName="TopRightButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, 0, Qt.AlignRight)

    @staticmethod
    def _load_failed(document, load_result):
        try:
            page_count = int(document.pageCount())
        except Exception:
            page_count = 0
        if page_count > 0:
            return False, ""

        status = document.status()
        status_name = str(getattr(status, "name", "") or "").strip().lower()
        status_text = str(status).strip().lower()
        if status_name in {"ready"} or status_text.endswith(".ready") or status_text == "ready":
            return False, ""

        name = getattr(load_result, "name", "")
        if isinstance(name, str) and name:
            normalized = name.strip().lower()
            if normalized in {"none", "none_", "noerror", "success"}:
                return False, ""
            return True, f"QtPdf load result: {name}"

        text = str(load_result).strip().lower()
        if text in {"0", "none", "none_", "noerror", "success"}:
            return False, ""
        if text.endswith(".none") or text.endswith(".none_") or text.endswith(".ready"):
            return False, ""
        return bool(text), f"QtPdf load result: {load_result}, status: {status}"


def preview_file(parent, path, *, mime_type=""):
    path = str(path or "").strip()
    if not path or not os.path.exists(path):
        AppMessageBox.warning(parent, "Preview File", f"The selected file could not be found.\n\n{path or '(missing path)'}")
        return False

    mime_type = str(mime_type or "").lower()
    extension = os.path.splitext(path)[1].lower()

    try:
        if mime_type.startswith("image/") or extension in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}:
            dialog = ImagePreviewDialog(path, parent)
            if not dialog.preview_ready:
                AppMessageBox.warning(parent, "Image Preview", f"The image file was found, but it could not be rendered.\n\n{path}")
                return False
            dialog.exec()
            return True

        if (mime_type == "application/pdf" or extension == ".pdf") and HAS_QT_PDF:
            dialog = PdfPreviewDialog(path, parent)
            if not dialog.preview_ready:
                AppMessageBox.warning(parent, "PDF Preview", f"The PDF file was found, but the in-app PDF viewer could not render it.\n\n{path}")
                return False
            dialog.exec()
            return True

        _open_externally(parent, path, mime_type=mime_type, extension=extension)
        return True
    except Exception as exc:
        AppMessageBox.critical(parent, "Preview File", f"The file could not be opened.\n\nFile:\n{path}\n\nReason:\n{exc}")
        return False


def _open_externally(parent, path, *, mime_type="", extension=""):
    if platform.system() == "Windows":
        os.startfile(path)
        AppMessageBox.information(parent, "Open File", f"Opened the file with the default system app.\n\nFile:\n{path}")
        return

    command = ["open", path] if platform.system() == "Darwin" else ["xdg-open", path]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        reason = (result.stderr or result.stdout or "Unknown error").strip()
        raise Exception(reason)

    fallback_reason = []
    if extension == ".pdf" and not HAS_QT_PDF:
        fallback_reason.append("QtPdf is not available")
    if mime_type and not mime_type.startswith("image/") and extension != ".pdf":
        fallback_reason.append(f"unsupported preview type: {mime_type or extension}")

    message = "Opened the file with the default system app."
    if fallback_reason:
        message += f"\n\nPreview fallback reason:\n{chr(10).join(fallback_reason)}"
    message += f"\n\nFile:\n{path}"
    AppMessageBox.information(parent, "Open File", message)
