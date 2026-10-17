import copy
import json
from pathlib import Path

import numpy as np
import pytest
import trimesh

from auxarc.carrier import (
    FitError,
    align_inputs,
    clip,
    correct_geometry,
    load_mesh,
    mesh_facts,
    require_solid,
    validate,
    volume,
)

ROOT = Path(__file__).parents[1]


def case():
    return json.loads((ROOT / "cases/glock-iwb-v1.json").read_text())


def box(lo, hi):
    return trimesh.creation.box(bounds=[lo, hi])


def test_clip_matches_independently_calculated_box_volume():
    m = clip(box([0, 0, 0], [10, 10, 10]), [2, 3, 4], [8, 9, 9])
    assert volume(m) == pytest.approx(6 * 6 * 5)
    assert np.allclose(m.bounds, [[2, 3, 4], [8, 9, 9]])


def test_empty_intersection_has_zero_volume():
    m = clip(box([0, 0, 0], [1, 1, 1]), [2, 2, 2], [3, 3, 3])
    assert volume(m) == 0


def test_invalid_mesh_is_rejected(tmp_path):
    m = box([0, 0, 0], [1, 1, 1])
    m.update_faces(np.arange(len(m.faces) - 1))
    path = tmp_path / "open.stl"
    m.export(path)
    with pytest.raises(FitError, match="watertight"):
        load_mesh(path)


def test_disconnected_carrier_is_rejected():
    m = trimesh.util.concatenate([box([0, 0, 0], [1, 1, 1]), box([2, 0, 0], [3, 1, 1])])
    with pytest.raises(FitError, match="single"):
        require_solid(m, "carrier", single=True)


def test_finite_mesh_and_positive_volume_required():
    m = box([0, 0, 0], [1, 1, 1])
    m.invert()
    with pytest.raises(FitError, match="positive"):
        require_solid(m, "carrier")


def test_alignment_is_rigid_and_does_not_mutate_inputs():
    meshes = {name: box([0, 0, 0], [1, 2, 3]) for name in ["carrier", "wing", "holster"]}
    originals = {name: m.vertices.copy() for name, m in meshes.items()}
    aligned = align_inputs(meshes, case(), "original")
    assert np.allclose(
        aligned["carrier"].vertices, originals["carrier"] + case()["carrier_translation"]
    )
    assert volume(aligned["wing"]) == pytest.approx(6)
    assert np.allclose(np.linalg.det(np.array(case()["wing_transform"])[:3, :3]), 1)
    for name, m in meshes.items():
        assert np.array_equal(m.vertices, originals[name])


def test_graft_replaces_front_and_preserves_back_without_global_scaling():
    c = copy.deepcopy(case())
    c.update(
        carrier_translation=[0, 0, 0],
        seam_y_aligned=0,
        graft_overlap=0.5,
        coupon_bounds_original=[[-2, -2, 0], [2, 2, 4]],
    )
    original = box([-2, -3, 0], [2, 2, 4])
    working = box([-1, -3, 0.1], [1, 1, 3.9])
    fixed, coupon = correct_geometry(original, working, c)
    # Rear half: 4*3*4. New front half: 2*1*3.8.
    assert volume(fixed) == pytest.approx(48 + 7.6)
    assert volume(clip(fixed, [-2, -3, 0], [2, -1, 4])) == pytest.approx(32)
    assert np.allclose(coupon.bounds[0], 0)
    assert mesh_facts(coupon)["single_solid"]


def synthetic_validation():
    c = copy.deepcopy(case())
    c.update(
        carrier_translation=[0, 0, 0],
        body_guard_y_original=-1,
        pin_axis=[0, 0, 0],
        pin_z_range=[0, 4],
        angles_deg=[0],
        axial_offsets_mm=[0],
    )
    carrier = box([2, -3, 0], [4, 1, 4])
    holster = box([-4, -3, 0], [-2, 1, 4])
    return c, carrier, holster


def test_validation_detects_body_loss():
    c, original, holster = synthetic_validation()
    shortened = box([2, -2, 0], [4, 1, 4])
    result = validate(shortened, original, holster, c)
    assert not result["checks"]["body_preserved"]
    assert result["body_difference_mm3"] == pytest.approx(8)


def test_validation_detects_pin_obstruction():
    c, original, holster = synthetic_validation()
    c["pin_axis"] = [3, 0, 0]
    result = validate(original, original, holster, c)
    assert not result["checks"]["straight_1_75_mm_pin_clear"]


def test_validation_detects_solid_collision():
    c, original, _ = synthetic_validation()
    result = validate(original, original, original, c)
    assert not result["checks"]["no_holster_interference_at_sampled_poses"]
    assert result["intersections"][0]["intersection_mm3"] == pytest.approx(32)


def test_validation_accepts_separated_parts_and_clear_pin():
    c, original, holster = synthetic_validation()
    result = validate(original, original, holster, c)
    assert all(result["checks"].values())
