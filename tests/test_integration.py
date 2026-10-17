"""Optional real-model tests; source meshes are never committed or uploaded by CI."""

import hashlib
import json
import os
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pytest
import trimesh

from auxarc import cli
from auxarc.carrier import load_mesh, sha256, volume
from auxarc.cli import COUPON, FULL, main, runtime_facts

ROOT = Path(__file__).parents[1]
pytestmark = pytest.mark.integration


def assert_json_near(actual, expected):
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for key in expected:
            assert_json_near(actual[key], expected[key])
    elif isinstance(expected, list):
        assert len(actual) == len(expected)
        for a, b in zip(actual, expected, strict=True):
            assert_json_near(a, b)
    elif isinstance(expected, float):
        assert actual == pytest.approx(expected, abs=1e-6, rel=1e-10)
    else:
        assert actual == expected


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
    evidence = json.loads((ROOT / "evidence/reference-manifest.json").read_text())
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["case_sha256"] == evidence["case_sha256"]
    for name, path in references.items():
        assert sha256(path) == evidence["inputs"][name]["sha256"]
    for filename in [FULL, COUPON]:
        assert_json_near(
            manifest["outputs"][filename]["mesh"], evidence["outputs"][filename]["mesh"]
        )
    for filename in ["original-validation.json", "corrected-validation.json"]:
        assert_json_near(
            json.loads((out / filename).read_text()),
            json.loads((ROOT / "evidence" / filename).read_text()),
        )
    contents = {p.name: p.read_bytes() for p in out.iterdir()}
    assert main(argv(references, out)) == 1
    assert "already exists" in capsys.readouterr().err
    assert contents == {p.name: p.read_bytes() for p in out.iterdir()}


def test_recorded_runtime_reproduces_both_output_hashes(references, tmp_path):
    evidence = json.loads((ROOT / "evidence/reference-manifest.json").read_text())
    dependencies = {name: version(name) for name in evidence["dependencies"]}
    if runtime_facts() != evidence["runtime"] or dependencies != evidence["dependencies"]:
        pytest.skip("Historical byte comparison requires the recorded runtime and dependencies")
    out = tmp_path / "build"
    assert main(argv(references, out)) == 0
    for filename in [FULL, COUPON]:
        assert sha256(out / filename) == evidence["outputs"][filename]["sha256"]


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
    original_out, aligned_out = tmp_path / "original-frame-build", tmp_path / "aligned-build"
    assert main(argv(paths, original_out, "original")) == 0
    assert main(argv(references, aligned_out)) == 0
    a, b = [load_mesh(out / FULL) for out in [original_out, aligned_out]]
    for left, right in [(a, b), (b, a)]:
        difference = trimesh.boolean.difference([left, right], engine="manifold")
        assert volume(difference) < 0.001


def test_reproduction_matches_previously_supplied_print_file(references, tmp_path):
    path = os.environ.get("AUXARC_PRINTED_STL")
    if not path:
        pytest.skip("Set AUXARC_PRINTED_STL to the previously supplied v1 carrier STL")
    out = tmp_path / "build"
    assert main(argv(references, out)) == 0
    regenerated, printed = [load_mesh(p) for p in [out / FULL, path]]
    for a, b in [(regenerated, printed), (printed, regenerated)]:
        difference = trimesh.boolean.difference([a, b], engine="manifold")
        assert volume(difference) < 0.0001
    assert np.allclose(regenerated.bounds, printed.bounds, rtol=0, atol=0.00001)


def test_manifest_hashes_the_same_snapshots_that_are_processed(references, tmp_path, monkeypatch):
    paths = {name: tmp_path / path.name for name, path in references.items()}
    snapshots = {name: path.read_bytes() for name, path in references.items()}
    for name, path in paths.items():
        path.write_bytes(snapshots[name])
    case_path = tmp_path / "case.json"
    case_bytes = (ROOT / "cases/glock-iwb-v1.json").read_bytes()
    case_path.write_bytes(case_bytes)
    real_load = cli.load_mesh

    def concurrent_change(path, data=None):
        if path == paths["carrier"]:
            path.write_bytes(b"changed after snapshot")
            case_path.write_text("{}")
        return real_load(path, data)

    monkeypatch.setattr(cli, "load_mesh", concurrent_change)
    out = tmp_path / "output"
    arguments = argv(paths, out)
    arguments[2] = str(case_path)
    assert main(arguments) == 0
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["case_sha256"] == hashlib.sha256(case_bytes).hexdigest()
    for name, data in snapshots.items():
        assert manifest["inputs"][name]["sha256"] == hashlib.sha256(data).hexdigest()
