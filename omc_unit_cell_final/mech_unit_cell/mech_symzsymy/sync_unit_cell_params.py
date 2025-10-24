from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Tuple


def load_final_params(json_path: Path) -> Dict[str, str]:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Ensure all values are strings (COMSOL parameter API accepts strings with units)
    return {str(k): str(v) for k, v in data.items()}


def planned_params_for(model_kind: str, base: Dict[str, str]) -> Dict[str, str]:
    """Compose the parameter set for mirror/defect/wg models.

    - mirror: n=17, d17/h17 <- d17_mir/h17_mir
    - defect: n=0, (no explicit d17/h17 override)
    - wg:     n=17, d17/h17 <- d17_wg/h17_wg
    """
    kind = model_kind.lower()
    params = dict(base)

    if kind == "mirror":
        params["n"] = "17"
        # Map the final mirror values into the actual d17/h17 knobs used in the MPH
        if "d17_mir" in base:
            params["d17"] = base["d17_mir"]
        if "h17_mir" in base:
            params["h17"] = base["h17_mir"]
    elif kind in ("defect", "mirror_defect", "defectmirror"):
        params["n"] = "0"
        # Intentionally do not override d17/h17; the model should derive geometry from n=0
    elif kind in ("wg", "waveguide", "mirror_wg", "mirrorwg"):
        params["n"] = "17"
        # Map the final waveguide values into d17/h17
        if "d17_wg" in base:
            params["d17"] = base["d17_wg"]
        if "h17_wg" in base:
            params["h17"] = base["h17_wg"]
    else:
        raise ValueError(f"Unknown model kind: {model_kind}")

    return params


def detect_param_mismatches(model, planned: Dict[str, str]) -> Dict[str, Tuple[str | None, str]]:
    """Return a dict of {name: (current, planned)} for differing parameters.

    Falls back to always-run if values cannot be read from the model.
    """
    diffs: Dict[str, Tuple[str | None, str]] = {}

    # Prefer a direct getter if available
    getter = None
    try:
        # Some mph versions support parameter(name) -> value
        if callable(getattr(model, "parameter")):
            getter = getattr(model, "parameter")
    except Exception:
        getter = None

    for k, v in planned.items():
        current_str: str | None = None
        try:
            if getter is not None:
                # type: ignore[misc]
                current_val = getter(str(k))  # may raise if unsupported
                if current_val is not None:
                    current_str = str(current_val)
        except Exception:
            current_str = None

        planned_str = str(v)
        # If we couldn't read, assume mismatch so we will update and run
        if current_str is None or current_str.strip() != planned_str.strip():
            diffs[k] = (current_str, planned_str)

    return diffs


def main(argv: list[str]) -> int:
    import argparse

    here = Path(__file__).resolve().parent
    # Repo root assumed two levels up from bdagger_final_simulations
    repo_root = here.parents[4]  # .../bdagger-project
    final_json = repo_root / "bdagger_final_simulations" / "final_geometry" / "final_dimensions.json"

    parser = argparse.ArgumentParser(description="Sync COMSOL unit cell params from final JSON and run if mismatched.")
    parser.add_argument("--json", type=Path, default=final_json, help="Path to final parameters JSON")
    parser.add_argument("--study", default="std1", help="COMSOL study tag to solve")
    parser.add_argument("--force", action="store_true", help="Force update and run even if no mismatch detected")
    parser.add_argument("--dry-run", action="store_true", help="Do not modify or run; just print planned changes")
    parser.add_argument("--save-solved", action="store_true", help="Save a solved copy of the model next to exports")
    parser.add_argument("--export-name", default=None, help="Optional export name to use; otherwise best-effort pick")
    parser.add_argument("--which", choices=["all", "mirror", "defect", "wg"], default="all", help="Which models to process")
    args = parser.parse_args(argv)

    # Import helper runner available in this repo
    sys.path.append(str(repo_root / "bdagger-inverse-design"))
    try:
        from comsol_runner import have_mph, ComsolUnavailable, list_exports  # type: ignore
    except Exception:
        have_mph = lambda: False  # type: ignore
        class ComsolUnavailable(Exception):  # type: ignore
            pass
        def list_exports(model):  # type: ignore
            return []

    # Load base parameters
    base_params = load_final_params(args.json)

    # Target models in this directory
    models = {
        "mirror": here / "unit_mech_sym_mirror.mph",
        "defect": here / "unit_mech_sym_mirror_defect.mph",
        "wg": here / "unit_mech_sym_mirror_wg.mph",
    }

    selected = list(models.keys()) if args.which == "all" else [args.which]

    # If no COMSOL API, just report what would happen
    if not have_mph():
        print("'mph' (COMSOL Python API) not available. Dry-report only.")
        for kind in selected:
            planned = planned_params_for(kind, base_params)
            print(f"[DRY] {kind}: would set {len(planned)} parameters; forced run={args.force}")
        return 0

    import mph  # type: ignore

    client = mph.start()
    try:
        for kind in selected:
            mph_path = models[kind]
            if not mph_path.exists():
                print(f"[SKIP] {kind}: model not found: {mph_path}")
                continue
            planned = planned_params_for(kind, base_params)

            model = client.load(str(mph_path))
            diffs = detect_param_mismatches(model, planned)

            if args.dry_run:
                print(f"[DRY] {kind}: {len(diffs)} param diffs")
                for k, (cur, new) in sorted(diffs.items()):
                    print(f"   - {k}: {cur!r} -> {new!r}")
                continue

            if not diffs and not args.force:
                print(f"[OK] {kind}: parameters already match; skipping solve")
                continue

            # Apply updates
            for k, (_, new) in diffs.items():
                model.parameter(str(k), str(new))

            # Build/mesh/solve
            try:
                model.build()
            except Exception:
                pass
            try:
                model.mesh()
            except Exception:
                pass
            print(f"[RUN] {kind}: solving study {args.study} with {len(diffs)} changes")
            model.solve(args.study)

            # Export band/global data if available
            exports = list_exports(model)
            export_name = args.export_name
            if export_name is None and exports:
                preferred = [e for e in exports if any(tok in e.lower() for tok in ("band", "global", "diag"))]
                export_name = preferred[0] if preferred else exports[0]
            if export_name:
                out_txt = mph_path.with_name(mph_path.stem + f"_{kind}_band.txt")
                try:
                    model.export(str(export_name), str(out_txt))
                    print(f"[OUT] {kind}: wrote {out_txt}")
                except Exception:
                    print(f"[WARN] {kind}: failed to export via '{export_name}'")

            # Optionally save a solved copy
            if args.save_solved:
                solved_path = mph_path.with_name(mph_path.stem + f"_{kind}_solved.mph")
                try:
                    model.save(str(solved_path))
                    print(f"[SAVE] {kind}: {solved_path}")
                except Exception:
                    print(f"[WARN] {kind}: save failed")

            # Clear the model from server memory before next
            try:
                client.clear()
            except Exception:
                pass

        return 0
    finally:
        try:
            client.clear()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

