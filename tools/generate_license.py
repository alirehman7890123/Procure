#!/usr/bin/env python3
import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utilities.license_core import ALGORITHM, PRODUCT_CODE, canonical_json, DOMAIN_SEPARATOR


def _hex_to_int(value: str) -> int:
    return int(value, 16)


def _digest_payload(payload: dict) -> bytes:
    from hashlib import sha256

    return sha256(DOMAIN_SEPARATOR + canonical_json(payload)).digest()


def load_private_key(path: Path) -> dict:
    try:
        key = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Failed to read private key file:\n{exc}")

    if not isinstance(key, dict):
        raise SystemExit("Private key file must contain a JSON object.")

    if key.get("alg") != ALGORITHM:
        raise SystemExit(f"Private key alg must be {ALGORITHM}.")

    if not key.get("n") or not key.get("d"):
        raise SystemExit("Private key file must contain hex fields 'n' and 'd'.")

    return key


def sign_payload(payload: dict, private_key: dict) -> str:
    digest_int = int.from_bytes(_digest_payload(payload), "big")
    n = _hex_to_int(private_key["n"])
    d = _hex_to_int(private_key["d"])
    signature_int = pow(digest_int, d, n)
    return format(signature_int, "x")


def load_request_payload(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Failed to read request file:\n{exc}")

    if not isinstance(data, dict):
        raise SystemExit("Request file must contain a JSON object.")

    fingerprint = str(data.get("machine_fingerprint") or "").strip()
    machine_id = str(data.get("machine_id") or "").strip()

    if not fingerprint:
        raise SystemExit("Request file does not contain machine_fingerprint.")

    return {
        "machine_fingerprint": fingerprint,
        "machine_id": machine_id,
        "request": data,
    }


def build_payload(args, machine_fingerprint: str) -> dict:
    issued_at = args.issued_at or date.today().isoformat()

    expires_at = args.expires_at
    if args.days is not None:
        expires_at = (date.fromisoformat(issued_at) + timedelta(days=args.days)).isoformat()

    payload = {
        "product": PRODUCT_CODE,
        "machine_fingerprint": machine_fingerprint,
        "license_type": args.license_type,
        "issued_at": issued_at,
    }

    if expires_at:
        payload["expires_at"] = expires_at
    if args.customer_name:
        payload["customer_name"] = args.customer_name
    if args.machine_id:
        payload["machine_id"] = args.machine_id
    if args.notes:
        payload["notes"] = args.notes

    return payload


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a signed Procure Medics license document for a client machine."
    )
    parser.add_argument(
        "--private-key",
        default=os.environ.get("PROCURE_PRIVATE_KEY_PATH", ""),
        help="Path to vendor private key JSON containing alg, n, and d.",
    )
    parser.add_argument(
        "--request-file",
        help="Path to a client machine request JSON copied from the activation dialog.",
    )
    parser.add_argument(
        "--fingerprint",
        help="Raw machine fingerprint if you are not using a request file.",
    )
    parser.add_argument(
        "--machine-id",
        help="Optional short machine ID to include for convenience.",
    )
    parser.add_argument(
        "--customer-name",
        default="",
        help="Customer name to embed in the payload.",
    )
    parser.add_argument(
        "--license-type",
        default="full",
        choices=["full", "demo", "trial"],
        help="License type value to embed in the payload.",
    )
    parser.add_argument(
        "--issued-at",
        help="ISO date like 2026-04-15. Defaults to today.",
    )
    parser.add_argument(
        "--expires-at",
        help="ISO expiry date like 2027-04-15.",
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Alternative to --expires-at. Adds N days to issued_at.",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional notes field to embed in the payload.",
    )
    parser.add_argument(
        "--output",
        help="Write the generated license JSON to this file.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    private_key_path = Path(args.private_key).expanduser() if args.private_key else None
    if not private_key_path:
        raise SystemExit("Provide --private-key or set PROCURE_PRIVATE_KEY_PATH.")
    if not private_key_path.exists():
        raise SystemExit(f"Private key file not found: {private_key_path}")

    request_info = None
    if args.request_file:
        request_info = load_request_payload(Path(args.request_file).expanduser())

    machine_fingerprint = str(args.fingerprint or "").strip()
    if request_info:
        machine_fingerprint = request_info["machine_fingerprint"]
        if not args.machine_id and request_info.get("machine_id"):
            args.machine_id = request_info["machine_id"]

    if not machine_fingerprint:
        raise SystemExit("Provide --fingerprint or --request-file.")

    if args.expires_at and args.days is not None:
        raise SystemExit("Use either --expires-at or --days, not both.")

    private_key = load_private_key(private_key_path)
    payload = build_payload(args, machine_fingerprint)
    document = {
        "payload": payload,
        "signature": sign_payload(payload, private_key),
    }
    raw_json = json.dumps(document, indent=2) + "\n"

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.write_text(raw_json, encoding="utf-8")
        print(f"License written to {output_path}")
    else:
        print(raw_json)


if __name__ == "__main__":
    main()
