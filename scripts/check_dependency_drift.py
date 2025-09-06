"""Simple dependency drift checker.

Compares declared service requirements against top-level constraints.txt.
Flags:
  * Version pins that differ from constraint
  * Core packages missing from a service (optional informational)

Run: python scripts/check_dependency_drift.py
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Tuple

ROOT = Path(__file__).resolve().parent.parent
CONSTRAINTS = ROOT / "constraints.txt"
SERVICE_REQ_GLOBS = [
    "[0-1][0-9]-*/requirements.txt",
    "1[0-6]-*/requirements.txt",
]
CORE_PACKAGES = {"fastapi", "uvicorn", "pydantic", "python-multipart"}

version_line_re = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)"
    r"(?P<op>==|>=|<=|~=|!=)?"
    r"(?P<ver>[A-Za-z0-9+_.-]*)"
)


def parse_requirements(path: Path) -> Dict[str, Tuple[str | None, str | None]]:
    out: Dict[str, Tuple[str | None, str | None]] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith(("#", '"')):
            continue
        match = version_line_re.match(line)
        if not match:
            continue
        name = match.group("name").lower()
        out[name] = (match.group("op"), match.group("ver"))
    return out


def parse_constraints() -> Dict[str, str]:
    data: Dict[str, str] = {}
    for line in CONSTRAINTS.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = version_line_re.match(line)
        if not match:
            continue
        if match.group("op") == "==":
            data[match.group("name").lower()] = match.group("ver")
    return data


def main() -> None:
    constraints = parse_constraints()
    issues: list[str] = []  # blocking version mismatch issues
    infos: list[str] = []   # non-blocking informational messages
    for glob in SERVICE_REQ_GLOBS:
        for req in ROOT.glob(glob):
            service = req.parent.name
            reqs = parse_requirements(req)
            # Check version mismatches for explicitly pinned packages
            for name, (op, ver) in reqs.items():
                if (
                    name in constraints
                    and op == "=="
                    and ver != constraints[name]
                ):
                    issues.append(
                        (
                            f"{service}: {name} pinned to {ver} "
                            f"but constraint is {constraints[name]}"
                        )
                    )
            # Core package presence (informational)
            missing = CORE_PACKAGES - set(reqs.keys())
            if missing:
                infos.append(
                    (
                        f"{service}: missing core packages (informational): "
                        f"{', '.join(sorted(missing))}"
                    )
                )
    if issues:
        print("Dependency drift issues detected:")
        for item in issues:
            print(" -", item)
    else:
        print("No blocking drift detected.")
    if infos:
        print("\nInformational:")
        for item in infos:
            print(" -", item)
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
