import json
import subprocess
from pathlib import Path

from auxarc.carrier import sha256

ROOT = Path(__file__).parents[1]


def test_evidence_case_hash_matches_published_case():
    evidence = json.loads((ROOT / "evidence/reference-manifest.json").read_text())
    assert sha256(ROOT / "cases/glock-iwb-v1.json") == evidence["case_sha256"]


def test_no_source_models_or_photos_are_tracked():
    files = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    restricted = {
        ".stl",
        ".3mf",
        ".glb",
        ".obj",
        ".ply",
        ".step",
        ".stp",
        ".f3d",
        ".scad",
        ".blend",
        ".jpg",
        ".jpeg",
        ".png",
        ".heic",
        ".webp",
        ".tif",
        ".tiff",
    }
    assert not [name for name in files if Path(name).suffix.lower() in restricted]
