import os
import json
import platform
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
from pathlib import Path


PRODUCT_CODE = "procure-medics"
ALGORITHM = "PROCURE-RSA-SHA256-V1"
DOMAIN_SEPARATOR = b"PROCURE_LICENSE_V1:"
DEFAULT_KEY_SIZE = 2048

APP_DIR = Path.home() / ".procure_medics"
LICENSE_PATH = APP_DIR / "license.dat"
PUBLIC_KEY_RELATIVE_PATH = Path("licensing") / "public_key.json"
PUBLIC_KEY_RELATIVE_VARIANTS = (
    PUBLIC_KEY_RELATIVE_PATH,
    Path("medic") / PUBLIC_KEY_RELATIVE_PATH,
)


def get_public_key_candidates() -> list[Path]:
    candidates: list[Path] = []

    env_override = os.environ.get("PROCURE_PUBLIC_KEY_PATH")
    if env_override:
        candidates.append(Path(env_override).expanduser())

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        meipass_path = Path(meipass)
        for relative_path in PUBLIC_KEY_RELATIVE_VARIANTS:
            candidates.append(meipass_path / relative_path)
            candidates.append(meipass_path / "_internal" / relative_path)

    executable = getattr(sys, "executable", "")
    if executable:
        exe_dir = Path(executable).resolve().parent
        for relative_path in PUBLIC_KEY_RELATIVE_VARIANTS:
            candidates.append(exe_dir / relative_path)
            candidates.append(exe_dir / "_internal" / relative_path)

    cwd = Path.cwd()
    for relative_path in PUBLIC_KEY_RELATIVE_VARIANTS:
        candidates.append(cwd / relative_path)

    source_base = Path(__file__).resolve().parent.parent
    for relative_path in PUBLIC_KEY_RELATIVE_VARIANTS:
        candidates.append(source_base / relative_path)
        candidates.append(source_base.parent / relative_path)

    unique_candidates: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        unique_candidates.append(path)
    return unique_candidates


def get_public_key_path() -> Path:
    for candidate in get_public_key_candidates():
        if candidate.exists():
            return candidate
    return get_public_key_candidates()[0]


class LicenseError(Exception):
    pass


class LicenseConfigurationError(LicenseError):
    pass


@dataclass
class LicenseValidationResult:
    valid: bool
    reason: str
    payload: dict | None = None


def canonical_json(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _hex_to_int(value: str) -> int:
    return int(value, 16)


def _digest_payload(payload: dict) -> bytes:
    return sha256(DOMAIN_SEPARATOR + canonical_json(payload)).digest()


def _run_command(command: list[str]) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=2, check=False)
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _read_first_existing(paths: list[str]) -> str:
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            continue
        try:
            value = path.read_text(encoding="utf-8").strip()
        except Exception:
            continue
        if value:
            return value
    return ""


def collect_machine_attributes() -> dict[str, str]:
    system = platform.system().lower()
    attrs: dict[str, str] = {
        "product": PRODUCT_CODE,
        "system": system,
        "machine": platform.machine().lower(),
    }

    mac = uuid.getnode()
    if mac:
        attrs["mac"] = f"{mac:012x}"

    if system == "windows":
        try:
            import winreg

            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
            machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            if machine_guid:
                attrs["machine_guid"] = str(machine_guid).strip().lower()
        except Exception:
            pass

        csproduct_uuid = _run_command(["wmic", "csproduct", "get", "uuid"])
        if csproduct_uuid:
            lines = [line.strip().lower() for line in csproduct_uuid.splitlines() if line.strip()]
            if len(lines) >= 2:
                attrs["hardware_uuid"] = lines[-1]
    else:
        machine_id = _read_first_existing(["/etc/machine-id", "/var/lib/dbus/machine-id"])
        if machine_id:
            attrs["machine_id"] = machine_id.lower()

        product_uuid = _read_first_existing(["/sys/class/dmi/id/product_uuid"])
        if product_uuid:
            attrs["hardware_uuid"] = product_uuid.lower()

        board_serial = _read_first_existing(["/sys/class/dmi/id/board_serial"])
        if board_serial:
            attrs["board_serial"] = board_serial.lower()

    return attrs


def get_machine_fingerprint() -> str:
    attrs = collect_machine_attributes()
    preferred_keys = [
        "product",
        "system",
        "machine",
        "machine_guid",
        "machine_id",
        "hardware_uuid",
        "board_serial",
    ]
    selected_pairs = [f"{key}={attrs[key]}" for key in preferred_keys if attrs.get(key)]
    if len(selected_pairs) < 4 and attrs.get("mac"):
        selected_pairs.append(f"mac={attrs['mac']}")
    material = "\n".join(selected_pairs)
    return sha256(material.encode("utf-8")).hexdigest().upper()


def get_machine_id_short() -> str:
    fingerprint = get_machine_fingerprint()
    parts = [fingerprint[index:index + 5] for index in range(0, 20, 5)]
    return "-".join(parts)


def get_machine_request_payload() -> dict:
    attrs = collect_machine_attributes()
    return {
        "product": PRODUCT_CODE,
        "machine_id": get_machine_id_short(),
        "machine_fingerprint": get_machine_fingerprint(),
        "attributes": attrs,
    }


def verify_payload_signature(payload: dict, signature_hex: str, public_key: dict) -> bool:
    if public_key.get("alg") != ALGORITHM:
        return False

    try:
        signature_int = _hex_to_int(signature_hex)
        n = _hex_to_int(public_key["n"])
        e = _hex_to_int(public_key["e"])
    except Exception:
        return False

    digest_int = int.from_bytes(_digest_payload(payload), "big")
    recovered = pow(signature_int, e, n)
    return recovered == digest_int


def parse_license_text(raw_text: str) -> dict:
    try:
        document = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise LicenseError("License file is not valid JSON.") from exc

    if not isinstance(document, dict):
        raise LicenseError("License file must contain an object.")
    if "payload" not in document or "signature" not in document:
        raise LicenseError("License file is missing payload or signature.")
    if not isinstance(document["payload"], dict):
        raise LicenseError("License payload must be an object.")
    if not isinstance(document["signature"], str) or not document["signature"].strip():
        raise LicenseError("License signature is missing.")
    return document


def save_license_text(raw_text: str) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    LICENSE_PATH.write_text(raw_text.strip() + "\n", encoding="utf-8")


def load_saved_license_text() -> str | None:
    if not LICENSE_PATH.exists():
        return None
    try:
        raw_text = LICENSE_PATH.read_text(encoding="utf-8").strip()
    except Exception:
        return None
    return raw_text or None


def load_public_key() -> dict:
    public_key_path = get_public_key_path()
    if not public_key_path.exists():
        checked_paths = "\n".join(str(path) for path in get_public_key_candidates())
        raise LicenseConfigurationError(
            "Public key is not configured. Checked these locations:\n"
            f"{checked_paths}"
        )

    try:
        public_key = json.loads(public_key_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise LicenseConfigurationError("Public key file could not be read.") from exc

    if not isinstance(public_key, dict) or not public_key.get("n") or not public_key.get("e"):
        raise LicenseConfigurationError("Public key file is incomplete.")
    return public_key


def _parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise LicenseError(f"Invalid ISO date: {value}") from exc


def validate_license_document(document: dict, today: date | None = None) -> LicenseValidationResult:
    try:
        public_key = load_public_key()
    except LicenseConfigurationError as exc:
        return LicenseValidationResult(False, str(exc))

    payload = document.get("payload") or {}
    signature = document.get("signature", "")

    if payload.get("product") != PRODUCT_CODE:
        return LicenseValidationResult(False, "License is for a different product.")

    if not verify_payload_signature(payload, signature, public_key):
        return LicenseValidationResult(False, "License signature is invalid.")

    expected_fingerprint = get_machine_fingerprint()
    if payload.get("machine_fingerprint") != expected_fingerprint:
        return LicenseValidationResult(False, "License does not match this machine.")

    today = today or datetime.utcnow().date()

    try:
        expires_at = _parse_iso_date(payload.get("expires_at"))
    except LicenseError as exc:
        return LicenseValidationResult(False, str(exc))

    if expires_at and expires_at < today:
        return LicenseValidationResult(False, "License has expired.", payload)

    issued_at = payload.get("issued_at")
    if issued_at:
        try:
            _parse_iso_date(issued_at)
        except LicenseError as exc:
            return LicenseValidationResult(False, str(exc))

    return LicenseValidationResult(True, "License is valid.", payload)


def load_and_validate_saved_license() -> LicenseValidationResult:
    raw_text = load_saved_license_text()
    if not raw_text:
        return LicenseValidationResult(False, "No license file found.")

    try:
        document = parse_license_text(raw_text)
    except LicenseError as exc:
        return LicenseValidationResult(False, str(exc))

    return validate_license_document(document)


def get_current_license_payload() -> dict | None:
    result = load_and_validate_saved_license()
    if not result.valid:
        return None
    return result.payload


def is_demo_license(payload: dict | None = None) -> bool:
    payload = payload or get_current_license_payload()
    if not payload:
        return False
    return str(payload.get("license_type") or "").lower() == "demo"


def get_license_days_remaining(payload: dict | None = None, today: date | None = None) -> int | None:
    payload = payload or get_current_license_payload()
    if not payload:
        return None

    expires_at = payload.get("expires_at")
    if not expires_at:
        return None

    parsed_expiry = _parse_iso_date(expires_at)
    today = today or datetime.utcnow().date()
    return (parsed_expiry - today).days
