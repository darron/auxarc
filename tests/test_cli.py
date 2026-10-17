import json
from pathlib import Path

import pytest
import trimesh

from auxarc.cli import main, publish_directory

CASE = Path(__file__).parents[1] / "cases/glock-iwb-v1.json"


def args_for(tmp_path):
    return [
        "build",
        "--case",
        str(CASE),
        "--output",
        str(tmp_path / "result"),
        "--carrier",
        str(tmp_path / "carrier.stl"),
        "--wing",
        str(tmp_path / "wing.stl"),
        "--holster",
        str(tmp_path / "holster.stl"),
    ]


def test_missing_inputs_return_nonzero_without_creating_output(tmp_path, capsys):
    assert main(args_for(tmp_path)) == 1
    assert "Input file does not exist" in capsys.readouterr().err
    assert not (tmp_path / "result").exists()


def test_wrong_source_variant_is_rejected_without_output(tmp_path, capsys):
    for name in ["carrier", "wing", "holster"]:
        trimesh.creation.box().export(tmp_path / f"{name}.stl")
    assert main(args_for(tmp_path)) == 1
    assert "bounds/face count differ" in capsys.readouterr().err
    assert not (tmp_path / "result").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("angles_deg", []),
        ("axial_offsets_mm", []),
        ("volume_tolerance_mm3", 0),
        ("graft_overlap", -1),
        ("carrier_translation", [0, 0, float("nan")]),
        ("wing_transform", [[1, 0], [0, 1]]),
        ("units", "inches"),
        ("body_guard_y_original", -80),
        ("source_signatures_original", {}),
        ("source_signatures_original", {"carrier": {"faces": 1, "bounds": [[0, 0, 0], [1, 1, 1]]}}),
        ("source_signatures_original", None),
        ("source_signatures_original", {"carrier": None, "wing": None, "holster": None}),
    ],
)
def test_invalid_case_is_rejected(tmp_path, capsys, field, value):
    config = json.loads(CASE.read_text())
    config[field] = value
    path = tmp_path / "case.json"
    path.write_text(json.dumps(config))
    argv = args_for(tmp_path)
    argv[2] = str(path)
    assert main(argv) == 1
    assert "Invalid case" in capsys.readouterr().err
    assert not (tmp_path / "result").exists()


def test_publication_cannot_replace_an_existing_empty_directory(tmp_path):
    stage, target = tmp_path / "stage", tmp_path / "target"
    stage.mkdir()
    (stage / "result.txt").write_text("validated")
    target.mkdir()
    inode = target.stat().st_ino
    with pytest.raises(FileExistsError):
        publish_directory(stage, target)
    assert target.stat().st_ino == inode
    assert list(target.iterdir()) == []


def test_publication_copies_validated_files_to_exclusively_created_directory(tmp_path):
    stage, target = tmp_path / "stage", tmp_path / "target"
    stage.mkdir()
    (stage / "result.txt").write_text("validated")
    publish_directory(stage, target)
    assert (target / "result.txt").read_text() == "validated"
