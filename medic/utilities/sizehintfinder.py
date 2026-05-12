from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QSizePolicy, QTableWidget, QWidget


@dataclass
class WidthPressureRow:
    widget: QWidget
    path: str
    class_name: str
    object_name: str
    width: int
    minimum_width: int
    size_hint_width: int
    minimum_size_hint_width: int
    horizontal_policy: int
    note: str


@dataclass
class SectionPressureRow:
    section: QWidget
    section_path: str
    section_label: str
    max_width_value: int
    culprit: WidthPressureRow


def _policy_name(policy_value: int) -> str:
    value = getattr(policy_value, "value", policy_value)
    mapping = {
        getattr(QSizePolicy.Fixed, "value", QSizePolicy.Fixed): "Fixed",
        getattr(QSizePolicy.Minimum, "value", QSizePolicy.Minimum): "Minimum",
        getattr(QSizePolicy.Maximum, "value", QSizePolicy.Maximum): "Maximum",
        getattr(QSizePolicy.Preferred, "value", QSizePolicy.Preferred): "Preferred",
        getattr(QSizePolicy.Expanding, "value", QSizePolicy.Expanding): "Expanding",
        getattr(QSizePolicy.MinimumExpanding, "value", QSizePolicy.MinimumExpanding): "MinimumExpanding",
        getattr(QSizePolicy.Ignored, "value", QSizePolicy.Ignored): "Ignored",
    }
    return mapping.get(value, str(value))


def _widget_label(widget: QWidget) -> str:
    class_name = widget.__class__.__name__
    object_name = widget.objectName().strip()
    return f"{class_name}#{object_name}" if object_name else class_name


def _table_header_note(table: QTableWidget) -> str:
    header = table.horizontalHeader()
    notes = []
    if header is not None:
        if header.stretchLastSection():
            notes.append("stretch-last")
        resize_modes = []
        for index in range(table.columnCount()):
            try:
                mode = getattr(header.sectionResizeMode(index), "value", header.sectionResizeMode(index))
            except TypeError:
                mode = getattr(header.sectionResizeMode(), "value", header.sectionResizeMode())
            mode_name = {
                getattr(QHeaderView.Interactive, "value", QHeaderView.Interactive): "Interactive",
                getattr(QHeaderView.Stretch, "value", QHeaderView.Stretch): "Stretch",
                getattr(QHeaderView.Fixed, "value", QHeaderView.Fixed): "Fixed",
                getattr(QHeaderView.ResizeToContents, "value", QHeaderView.ResizeToContents): "ResizeToContents",
            }.get(mode, str(mode))
            resize_modes.append(mode_name)
        if resize_modes:
            notes.append("modes=" + ",".join(resize_modes))
    if table.columnCount():
        column_widths = [str(table.columnWidth(i)) for i in range(table.columnCount())]
        notes.append("cols=" + ",".join(column_widths))
    return " | ".join(notes)


def _describe_widget(widget: QWidget, path: str) -> WidthPressureRow:
    size_hint = widget.sizeHint()
    minimum_size_hint = widget.minimumSizeHint()
    size_policy = widget.sizePolicy()

    note_parts = []
    if isinstance(widget, QTableWidget):
        note_parts.append(_table_header_note(widget))
    note = " | ".join(part for part in note_parts if part)

    return WidthPressureRow(
        widget=widget,
        path=path,
        class_name=widget.__class__.__name__,
        object_name=widget.objectName().strip(),
        width=int(widget.width()),
        minimum_width=int(widget.minimumWidth()),
        size_hint_width=int(size_hint.width()),
        minimum_size_hint_width=int(minimum_size_hint.width()),
        horizontal_policy=getattr(size_policy.horizontalPolicy(), "value", size_policy.horizontalPolicy()),
        note=note,
    )


def _collect_widget_rows(widget: QWidget, path: str = "") -> list[WidthPressureRow]:
    label = _widget_label(widget)
    current_path = f"{path} > {label}" if path else label
    rows = [_describe_widget(widget, current_path)]
    for child in widget.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
        rows.extend(_collect_widget_rows(child, current_path))
    return rows


def _row_peak_width(row: WidthPressureRow) -> int:
    return max(row.minimum_width, row.size_hint_width, row.minimum_size_hint_width)


def print_size_hints(widget: QWidget, indent: int = 0):
    """Recursively print size, hint, minimums, and policy for a widget tree."""
    prefix = " " * indent
    row = _describe_widget(widget, _widget_label(widget))
    policy_name = _policy_name(row.horizontal_policy)
    object_suffix = f" objectName={row.object_name!r}" if row.object_name else ""
    extra = f" note={row.note}" if row.note else ""
    print(
        f"{prefix}{row.class_name}:{object_suffix} "
        f"width={row.width} minWidth={row.minimum_width} "
        f"sizeHintW={row.size_hint_width} minSizeHintW={row.minimum_size_hint_width} "
        f"policy={policy_name}{extra}"
    )
    for child in widget.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
        print_size_hints(child, indent + 2)


def find_width_pressure(
    widget: QWidget,
    *,
    threshold: int = 900,
    include_size_hint: bool = True,
    include_minimum_size_hint: bool = True,
) -> list[WidthPressureRow]:
    """
    Return widgets whose width-related values exceed the threshold.

    This is meant for hunting widgets that stop a page from fitting cleanly
    inside a target working width such as 900-1000px.
    """
    matches = []
    for row in _collect_widget_rows(widget):
        exceeds = row.minimum_width >= threshold
        if include_size_hint:
            exceeds = exceeds or row.size_hint_width >= threshold
        if include_minimum_size_hint:
            exceeds = exceeds or row.minimum_size_hint_width >= threshold
        if exceeds:
            matches.append(row)
    matches.sort(
        key=lambda item: (
            _row_peak_width(item),
            item.path,
        ),
        reverse=True,
    )
    return matches


def find_section_width_pressure(
    widget: QWidget,
    *,
    threshold: int = 900,
) -> list[SectionPressureRow]:
    """
    Group width pressure by each direct child section of a page/widget.

    This is useful when a page has a few top-level content blocks and you want
    to know which section contains the descendant that is actually forcing the width.
    """
    section_rows: list[SectionPressureRow] = []
    root_label = _widget_label(widget)
    for child in widget.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
        child_rows = _collect_widget_rows(child, root_label)
        if not child_rows:
            continue
        culprit = max(child_rows, key=_row_peak_width)
        peak = _row_peak_width(culprit)
        if peak >= threshold:
            section_rows.append(
                SectionPressureRow(
                    section=child,
                    section_path=culprit.path.split(" > ")[1] if " > " in culprit.path else culprit.path,
                    section_label=_widget_label(child),
                    max_width_value=peak,
                    culprit=culprit,
                )
            )
    section_rows.sort(key=lambda item: (item.max_width_value, item.section_label), reverse=True)
    return section_rows


def print_width_pressure(
    widget: QWidget,
    *,
    threshold: int = 900,
    limit: int | None = 40,
):
    """Print the widgets creating width pressure beyond the target threshold."""
    rows = find_width_pressure(widget, threshold=threshold)
    print(f"Width pressure report for {_widget_label(widget)} | threshold={threshold}")
    if not rows:
        print("  No widgets exceeded the threshold.")
        return

    shown = rows if limit is None else rows[:limit]
    for row in shown:
        policy_name = _policy_name(row.horizontal_policy)
        object_suffix = f"#{row.object_name}" if row.object_name else ""
        extra = f" | {row.note}" if row.note else ""
        print(
            "  "
            f"{row.class_name}{object_suffix} | minW={row.minimum_width} "
            f"sizeHintW={row.size_hint_width} minSizeHintW={row.minimum_size_hint_width} "
            f"policy={policy_name}{extra}\n"
            f"    {row.path}"
        )

    if limit is not None and len(rows) > limit:
        print(f"  ... {len(rows) - limit} more widget(s) exceeded the threshold.")


def print_top_width_culprits(
    widget: QWidget,
    *,
    threshold: int = 900,
    limit: int = 10,
):
    """Convenience alias focused on the worst width offenders."""
    print_width_pressure(widget, threshold=threshold, limit=limit)


def print_section_width_pressure(
    widget: QWidget,
    *,
    threshold: int = 900,
    limit: int | None = 20,
):
    """Print the widest direct child sections of a page/widget."""
    rows = find_section_width_pressure(widget, threshold=threshold)
    print(f"Section width report for {_widget_label(widget)} | threshold={threshold}")
    if not rows:
        print("  No direct child sections exceeded the threshold.")
        return

    shown = rows if limit is None else rows[:limit]
    for row in shown:
        culprit = row.culprit
        policy_name = _policy_name(culprit.horizontal_policy)
        extra = f" | {culprit.note}" if culprit.note else ""
        print(
            "  "
            f"{row.section_label} | sectionPeak={row.max_width_value} | "
            f"culprit={culprit.class_name}"
            f"{('#' + culprit.object_name) if culprit.object_name else ''} "
            f"minW={culprit.minimum_width} sizeHintW={culprit.size_hint_width} "
            f"minSizeHintW={culprit.minimum_size_hint_width} policy={policy_name}{extra}\n"
            f"    culprit-path: {culprit.path}"
        )

    if limit is not None and len(rows) > limit:
        print(f"  ... {len(rows) - limit} more section(s) exceeded the threshold.")


# Usage examples:
# print_size_hints(page_widget)
# print_width_pressure(page_widget, threshold=900)
# print_top_width_culprits(page_widget, threshold=1000, limit=15)
# print_section_width_pressure(page_widget, threshold=1000)
