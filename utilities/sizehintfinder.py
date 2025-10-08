from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt

def print_size_hints(widget: QWidget, indent: int = 0):
    """Recursively print sizeHint() and sizePolicy() for a widget and its children."""
    prefix = " " * indent
    sh = widget.sizeHint()
    sp = widget.sizePolicy()
    print(f"{prefix}{widget.__class__.__name__}: "
          f"sizeHint={sh}, "
          f"policy=({sp.horizontalPolicy()}, {sp.verticalPolicy()})")

    for child in widget.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
        print_size_hints(child, indent + 2)



# Usage
# Example: check your ProfilePage
# profile = ProfilePage()
# print_size_hints(profile)






