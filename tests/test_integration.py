"""Optional real-model tests; source meshes are never committed or uploaded by CI."""

import json
import os
from pathlib import Path

import numpy as np
import pytest
import trimesh

from auxarc.carrier import load_mesh, volume
from auxarc.cli import COUPON, FULL, main

ROOT = Path(__file__).parents[1]
pytestmark = pytest.mark.integration


@pytest.fixture
def references():
    directory = os.environ.get("AUXARC_REFERENCE_DIR")
    if not directory:
        pytest.skip("Set AUXARC_REFERENCE_DIR to local saved aligned reference meshes")
    p = Path(directory)
    return {
        name: p / filename
        for name, filename in {
            "carrier": "carrier_aligned.stl",
            "wing": "wing_aligned.stl",
            "holster": "holster_reference.stl",
        }.items()
    }


def argv(paths, output, frame="aligned"):
    result = [
        "build",
        "--case",
        str(ROOT / "cases/glock-iwb-v1.json"),
        "--frame",
        frame,
        "--output",
        str(output),
    ]
    for name, path in paths.items():
        result += [f"--{name}", str(path)]
    return result


def test_reference_build_and_already_existing_output(references, tmp_path, capsys):
    out = tmp_path / "build"
    assert main(argv(references, out)) == 0
    original = json.loads((out / "original-validation.json").read_text())
    fixed = json.loads((out / "corrected-validation.json").read_text())
    assert original["intersections"][0]["intersection_mm3"] == pytest.approx(28.69258, abs=0.001)
    assert not original["checks"]["no_holster_interference_at_sampled_poses"]
    assert all(fixed["checks"].values())
    assert fixed["body_difference_mm3"] < 0.0001
    assert load_mesh(out / COUPON).is_volume
    contents = {p.name: p.read_bytes() for p in out.iterdir()}
    assert main(argv(references, out)) == 1
    assert "already exists" in capsys.readouterr().err
    assert contents == {p.name: p.read_bytes() for p in out.iterdir()}


def test_original_coordinate_input_path(references, tmp_path):
    config = json.loads((ROOT / "cases/glock-iwb-v1.json").read_text())
    paths = {}
    for name, path in references.items():
        mesh = load_mesh(path)
        if name == "carrier":
            mesh.apply_translation(-np.array(config["carrier_translation"]))
        if name == "wing":
            mesh.apply_transform(np.linalg.inv(config["wing_transform"]))
        paths[name] = tmp_path / f"{name}.stl"
        mesh.export(paths[name])
    assert main(argv(paths, tmp_path / "original-frame-build", "original")) == 0


def test_reproduction_matches_physically_tested_full_model(references, tmp_path):
    path = os.environ.get("AUXARC_PRINTED_STL")
    if not path:
        pytest.skip("Set AUXARC_PRINTED_STL to the successfully printed v1 full carrier")
    out = tmp_path / "build"
    assert main(argv(references, out)) == 0
    regenerated, printed = [load_mesh(p) for p in [out / FULL, path]]
    for a, b in [(regenerated, printed), (printed, regenerated)]:
        difference = trimesh.boolean.difference([a, b], engine="manifold")
        assert volume(difference) < 0.0001
    assert np.allclose(regenerated.bounds, printed.bounds, rtol=0, atol=0.00001)
