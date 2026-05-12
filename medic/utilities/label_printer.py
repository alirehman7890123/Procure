import shutil
import subprocess
from typing import Optional, Tuple


def send_label_print_command(
    code: str,
    qty: int,
    printer_name: Optional[str] = None,
    dry_run: bool = True,
) -> Tuple[bool, str]:
    """Send a label print command for a barcode code and quantity.

    This utility is intentionally not wired into any workflow yet.
    It can be called later from purchase save flow after commit.

    Args:
        code: Product barcode code to print on label.
        qty: Number of labels to print.
        printer_name: Optional printer queue name for lpr.
        dry_run: If True, does not print and only returns the command preview.

    Returns:
        (success, message)
    """
    code = (code or "").strip()
    if not code:
        return False, "Code is required."

    try:
        qty = int(qty)
    except (TypeError, ValueError):
        return False, "Quantity must be a valid integer."

    if qty <= 0:
        return False, "Quantity must be greater than zero."

    lpr_path = shutil.which("lpr")
    if not lpr_path:
        return False, "lpr command not found. Install CUPS/lpr first."

    # Minimal text label payload. You can replace this with ZPL/EPL/TSPL later.
    lines = [f"BARCODE: {code}"] * qty
    payload = "\n".join(lines) + "\n"

    cmd = [lpr_path]
    if printer_name:
        cmd.extend(["-P", printer_name])

    if dry_run:
        return True, f"DRY RUN: {' '.join(cmd)} | labels={qty} | code={code}"

    try:
        proc = subprocess.run(
            cmd,
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )
    except Exception as ex:
        return False, f"Print command failed to run: {ex}"

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "Unknown print error").strip()
        return False, f"Print failed: {err}"

    out = (proc.stdout or "").strip()
    return True, out or f"Sent {qty} label(s) for code {code}."
