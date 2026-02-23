#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LOCALES_DIR = ROOT / "quickbib" / "locales"
BASE_FILE = LOCALES_DIR / "en.json"


def _load_json(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a JSON object")

    cleaned: dict[str, str] = {}
    for key, value in data.items():
        if not isinstance(key, str):
            raise ValueError(f"{path}: all keys must be strings")
        if not isinstance(value, str):
            raise ValueError(f"{path}: value for key '{key}' must be a string")
        cleaned[key] = value
    return cleaned


def main() -> int:
    if not BASE_FILE.exists():
        print(f"Missing base translation file: {BASE_FILE}")
        return 1

    base = _load_json(BASE_FILE)
    base_keys = set(base.keys())

    locale_files = sorted(LOCALES_DIR.glob("*.json"))
    if not locale_files:
        print(f"No locale files found in {LOCALES_DIR}")
        return 1

    failed = False
    for locale_file in locale_files:
        data = _load_json(locale_file)
        keys = set(data.keys())

        missing = sorted(base_keys - keys)
        extra = sorted(keys - base_keys)

        if missing or extra:
            failed = True
            print(f"{locale_file}:")
            if missing:
                print(f"  missing keys ({len(missing)}):")
                for key in missing:
                    print(f"    - {key}")
            if extra:
                print(f"  extra keys ({len(extra)}):")
                for key in extra:
                    print(f"    - {key}")

    if failed:
        return 1

    print(f"All translation files are valid ({len(locale_files)} locale file(s)).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(exc)
        raise SystemExit(1)
