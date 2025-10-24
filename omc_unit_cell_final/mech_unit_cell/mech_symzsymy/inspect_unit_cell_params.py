from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
FINAL_JSON = REPO / "bdagger_final_simulations" / "final_geometry" / "final_dimensions.json"

MODELS = {
    "mirror": HERE / "unit_mech_sym_mirror.mph",
    "defect": HERE / "unit_mech_sym_mirror_defect.mph",
    "wg": HERE / "unit_mech_sym_mirror_wg.mph",
}


def have_mph() -> bool:
    try:
        import mph  # noqa: F401
        return True
    except Exception:
        return False


def export_params_via_mph(mph_path: Path) -> Dict[str, str]:
    import mph  # type: ignore
    client = mph.start()
    try:
        model = client.load(str(mph_path))
        params: Dict[str, str] = {}
        # Try Python-side accessor first
        try:
            p = model.parameters()  # type: ignore[attr-defined]
            if isinstance(p, dict) and p:
                params = {str(k): str(v) for k, v in p.items()}
        except Exception:
            pass
        # Fallback to Java API
        if not params:
            jparam = model.java.param()
            tags = None
            for m in ("tags", "getTags"):
                if hasattr(jparam, m):
                    tags = getattr(jparam, m)()
                    break
            if tags is None:
                raise RuntimeError("Cannot enumerate parameter tags (Java API).")
            for t in list(tags):
                params[str(t)] = str(jparam.get(str(t)))
        return params
    finally:
        try:
            client.clear()
        except Exception:
            pass


def main(argv: list[str]) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Inspect current parameters from unit cell MPH files and print them.")
    ap.add_argument("--which", choices=["all", "mirror", "defect", "wg"], default="all")
    ap.add_argument("--save-json", action="store_true", help="Also save per-model parameter JSON next to the MPH")
    args = ap.parse_args(argv)

    # Sanity: verify models exist
    selected = list(MODELS.keys()) if args.which == "all" else [args.which]
    missing = [k for k in selected if not MODELS[k].exists()]
    if missing:
        print(f"Missing MPH files for: {', '.join(missing)}", file=sys.stderr)
        return 2

    if not have_mph():
        print("The 'mph' package (COMSOL Python API) is not available. Install it and ensure COMSOL server is accessible.")
        return 2

    for kind in selected:
        path = MODELS[kind]
        try:
            params = export_params_via_mph(path)
        except Exception as e:
            print(f"[{kind}] Failed to read parameters: {e}")
            continue
        print(f"[{kind}] {path.name} — {len(params)} parameters")
        for k, v in sorted(params.items(), key=lambda kv: kv[0].lower()):
            print(f"  {k} = {v}")
        if args.save_json:
            out = path.with_suffix("")
            out = out.with_name(out.name + "_parameters.json")
            out.write_text(json.dumps(params, indent=2), encoding="utf-8")
            print(f"  -> wrote {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

