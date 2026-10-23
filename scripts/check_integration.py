"""Structural checks for the Innosonix integration.

Validates that everything Home Assistant expects to find is actually present,
without needing Home Assistant installed:

- every platform listed in const.PLATFORMS has a matching platform module
- manifest.json is valid JSON, its domain matches the package directory,
  and config_flow.py exists when the manifest declares config_flow
- strings.json and translations/en.json are valid JSON and contain a
  section for every platform

Exits non-zero on the first problem found.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = REPO_ROOT / "custom_components" / "innosonix"


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def main() -> None:
    if not PACKAGE_DIR.is_dir():
        fail(f"integration directory not found: {PACKAGE_DIR}")

    # --- PLATFORMS <-> platform modules ---------------------------------
    const_file = PACKAGE_DIR / "const.py"
    tree = ast.parse(const_file.read_text(encoding="utf-8"))
    platform_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PLATFORMS":
                    if not isinstance(node.value, (ast.List, ast.Tuple)):
                        fail("PLATFORMS must be a list/tuple of Platform values")
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Attribute):
                            # Home Assistant's Platform enum values are the lowercase
                            # member names (e.g. Platform.BINARY_SENSOR -> "binary_sensor").
                            platform_names.append(elt.attr.lower())
                        elif isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            platform_names.append(elt.value)
                        else:
                            fail(f"cannot determine platform name from: {ast.unparse(elt)}")
    if not platform_names:
        fail("no PLATFORMS assignment found in const.py")

    print(f"PLATFORMS: {', '.join(platform_names)}")
    for name in platform_names:
        module = PACKAGE_DIR / f"{name}.py"
        if not module.is_file():
            fail(f"platform module missing: custom_components/innosonix/{name}.py")
        print(f"  OK {name}.py")

    # --- manifest.json ---------------------------------------------------
    manifest_path = PACKAGE_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("domain") != PACKAGE_DIR.name:
        fail(f"manifest domain {manifest.get('domain')!r} != directory name {PACKAGE_DIR.name!r}")
    if not manifest.get("version"):
        fail("manifest.json is missing 'version'")
    print(f"manifest OK (domain={manifest['domain']}, version={manifest['version']})")

    if manifest.get("config_flow") and not (PACKAGE_DIR / "config_flow.py").is_file():
        fail("manifest declares config_flow but config_flow.py is missing")
    print("  OK config_flow.py")

    # --- strings / translations -------------------------------------------
    for rel in ("strings.json", "translations/en.json"):
        path = PACKAGE_DIR / rel
        if not path.is_file():
            fail(f"missing {rel}")
        data = json.loads(path.read_text(encoding="utf-8"))
        entity = data.get("entity", {})
        for name in platform_names:
            if name not in entity:
                fail(f"{rel} has no 'entity.{name}' section (platform module present but strings missing?)")
        print(f"{rel} OK")

    print("All structural checks passed.")


if __name__ == "__main__":
    main()
