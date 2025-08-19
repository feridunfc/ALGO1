import os
import sys
import json
from typing import Dict, List, Tuple

def _scan_file(path: str) -> Dict[str, bool]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return {
        "ohlc_validation": ("def validate_ohlc" in content),
        "timezone_handling": ("tz_localize" in content or "tz_convert" in content),
        "adjustments": ("apply_split" in content or "apply_dividend" in content),
    }

def verify_implementation(repo_path: str) -> List[Tuple[str, Dict[str, bool]]]:
    required_files = [
        "data/loader.py",
        "data/validation.py",
        "data/corporate_actions.py",
    ]
    implemented = []
    for f in required_files:
        p = os.path.join(repo_path, f)
        if os.path.exists(p):
            implemented.append((f, _scan_file(p)))
        else:
            implemented.append((f, {"exists": False, "ohlc_validation": False, "timezone_handling": False, "adjustments": False}))
    return implemented

def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    res = verify_implementation(repo)
    print("=== Data Quality Implementation Report ===")
    for f, checks in res:
        print(f"- {f}")
        if "exists" in checks and not checks["exists"]:
            print("   ✗ file missing")
            continue
        for k, v in checks.items():
            print(f"   {'✓' if v else '✗'} {k}")
    print("\nJSON:")
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
