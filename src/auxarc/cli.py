"""CLI publishing outputs only after the exported files pass geometry checks."""

import argparse
import hashlib
import json
import platform
import shutil
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

from .carrier import (
    FitError,
    align_inputs,
    correct_geometry,
    load_mesh,
    mesh_facts,
    require_solid,
    sha256,
    source_signatures_match,
    validate,
    validate_replacement,
)
from .config import validate_config

FULL = "Mag_Carrier_Corrected_Hinge_v1.stl"
COUPON = "Carrier_Hinge_Fit_Test_v1.stl"


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def runtime_facts():
    return {
        "python": platform.python_version(),
        "system": platform.system(),
        "machine": platform.machine(),
        "platform": platform.platform(),
    }


def publish_directory(stage, destination):
    # mkdir is an exclusive reservation; rename could replace an existing empty
    # directory on POSIX. Exclusive file creation also prevents overwriting files
    # another process might add after this reservation.
    destination.mkdir()
    for source in stage.iterdir():
        with source.open("rb") as reader, (destination / source.name).open("xb") as writer:
            shutil.copyfileobj(reader, writer)


def build(args):
    case_bytes = args.case.read_bytes()
    config = json.loads(case_bytes)
    validate_config(config)
    paths = {name: getattr(args, name) for name in ["carrier", "wing", "holster"]}
    snapshots = {
        name: path.read_bytes() if path.is_file() else None for name, path in paths.items()
    }
    meshes = {name: load_mesh(path, snapshots[name]) for name, path in paths.items()}
    originals = source_signatures_match(meshes, config, args.frame)
    aligned = align_inputs(meshes, config, args.frame)
    if args.output.exists():
        raise FitError("Output already exists; choose a new directory (nothing overwritten)")
    corrected, coupon = correct_geometry(aligned["carrier"], aligned["wing"], config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".auxarc-", dir=args.output.parent) as temporary:
        stage = Path(temporary) / "result"
        stage.mkdir()
        corrected.export(stage / FULL)
        coupon.export(stage / COUPON)
        # Reload the actual print files, rather than only testing in-memory meshes.
        corrected_export = load_mesh(stage / FULL)
        coupon_export = load_mesh(stage / COUPON)
        require_solid(coupon_export, "exported hinge test", single=True)
        original_report = validate(
            originals["carrier"], originals["carrier"], aligned["holster"], config
        )
        corrected_report = validate(
            corrected_export, originals["carrier"], aligned["holster"], config
        )
        replacement = validate_replacement(corrected_export, coupon_export, aligned["wing"], config)
        corrected_report["replacement"] = replacement
        corrected_report["checks"].update(replacement["checks"])
        if not all(corrected_report["checks"].values()):
            raise FitError(
                "Export failed geometry checks: "
                + ", ".join(k for k, passed in corrected_report["checks"].items() if not passed)
            )
        if original_report["checks"]["no_holster_interference_at_sampled_poses"]:
            raise FitError("Original collision was not reproduced; check inputs and coordinates")
        write_json(stage / "original-validation.json", original_report)
        write_json(stage / "corrected-validation.json", corrected_report)
        manifest = {
            "case": config["case"],
            "input_frame": args.frame,
            "runtime": runtime_facts(),
            "case_sha256": hashlib.sha256(case_bytes).hexdigest(),
            "inputs": {
                name: {
                    "file": path.name,
                    "sha256": hashlib.sha256(snapshots[name]).hexdigest(),
                    "mesh": mesh_facts(meshes[name]),
                }
                for name, path in paths.items()
            },
            "dependencies": {
                name: version(name) for name in ["numpy", "trimesh", "manifold3d", "networkx"]
            },
            "outputs": {
                name: {"sha256": sha256(stage / name), "mesh": mesh_facts(mesh)}
                for name, mesh in [(FULL, corrected_export), (COUPON, coupon_export)]
            },
        }
        write_json(stage / "manifest.json", manifest)
        publish_directory(stage, args.output)
    print(f"PASS: {FULL} and {COUPON}; original collision reproduced; exported fit checks pass.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Reproduce the documented glock-iwb-v1 hinge graft"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("build", help="build and validate using locally supplied source meshes")
    p.add_argument("--case", type=Path, required=True)
    for name in ["carrier", "wing", "holster"]:
        p.add_argument(f"--{name}", type=Path, required=True)
    p.add_argument("--frame", choices=["original", "aligned"], default="original")
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        return build(args)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
