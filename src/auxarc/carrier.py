"""Rigid alignment, a Boolean hinge graft, and measured fit checks.

No model geometry is embedded here. Constants belong to the documented case.
"""

import hashlib
import io
from pathlib import Path

import numpy as np
import trimesh


class FitError(ValueError):
    """An input or generated mesh does not meet the documented case contract."""


def volume(mesh):
    return abs(float(mesh.volume)) if len(mesh.faces) else 0.0


def mesh_facts(mesh):
    return {
        "faces": len(mesh.faces),
        "bounds_mm": mesh.bounds.tolist() if len(mesh.faces) else None,
        "volume_mm3": volume(mesh),
        "watertight": bool(mesh.is_watertight),
        "consistent_winding": bool(mesh.is_winding_consistent),
        "single_solid": len(mesh.split()) == 1,
    }


def require_solid(mesh, name, single=False):
    if not isinstance(mesh, trimesh.Trimesh) or not len(mesh.faces):
        raise FitError(f"{name}: expected a nonempty triangle mesh")
    if not np.isfinite(mesh.vertices).all():
        raise FitError(f"{name}: vertices must be finite")
    if not mesh.is_watertight:
        raise FitError(f"{name}: mesh must be watertight")
    if not mesh.is_winding_consistent:
        raise FitError(f"{name}: mesh winding must be consistent")
    if mesh.volume <= 0:
        raise FitError(f"{name}: mesh must have positive signed volume")
    if single and len(mesh.split()) != 1:
        raise FitError(f"{name}: expected a single connected solid")


def load_mesh(path, data=None):
    path = Path(path)
    if data is None and not path.is_file():
        raise FitError(f"Input file does not exist: {path.name}")
    if data is None:
        data = path.read_bytes()
    mesh = trimesh.load_mesh(io.BytesIO(data), file_type=path.suffix.lstrip("."))
    require_solid(mesh, path.name)
    return mesh


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def symmetric_difference_volume(a, b):
    return sum(
        volume(trimesh.boolean.difference([x, y], engine="manifold")) for x, y in [(a, b), (b, a)]
    )


def validate_replacement(candidate_original, coupon, wing_aligned, config):
    """Check positive hinge presence, plus the exported coupon's intended extent."""
    candidate = candidate_original.copy()
    candidate.apply_translation(config["carrier_translation"])
    lower, upper = _bounds_covering(candidate, wing_aligned)
    # Exclude the body/blend boundary; beyond it the donor must be unchanged.
    lower[1] = config["seam_y_aligned"] + 0.001
    actual, expected = [clip(m, lower, upper) for m in [candidate, wing_aligned]]
    hinge_difference = symmetric_difference_volume(actual, expected)
    expected_coupon = clip(candidate_original, *config["coupon_bounds_original"])
    expected_coupon.apply_transform(np.array(config["coupon_orientation"], dtype=float))
    expected_coupon.apply_translation(-expected_coupon.bounds[0])
    coupon_difference = symmetric_difference_volume(coupon, expected_coupon)
    tol = config["volume_tolerance_mm3"]
    return {
        "checks": {
            "donor_hinge_preserved": hinge_difference < tol,
            "coupon_matches_intended_cut": coupon_difference < tol,
        },
        "hinge_difference_mm3": hinge_difference,
        "coupon_difference_mm3": coupon_difference,
    }


def align_inputs(meshes, config, frame):
    result = {name: mesh.copy() for name, mesh in meshes.items()}
    if frame == "original":
        result["carrier"].apply_translation(config["carrier_translation"])
        result["wing"].apply_transform(np.array(config["wing_transform"], dtype=float))
    elif frame != "aligned":
        raise FitError(f"Unsupported input frame: {frame}")
    return result


def source_signatures_match(meshes, config, frame):
    """Coarse rejection of wrong variants, NOT a content identity guarantee."""
    original = {name: mesh.copy() for name, mesh in meshes.items()}
    if frame == "aligned":
        original["carrier"].apply_translation(-np.array(config["carrier_translation"]))
        original["wing"].apply_transform(np.linalg.inv(config["wing_transform"]))
    for name, expected in config["source_signatures_original"].items():
        mesh = original[name]
        if len(mesh.faces) != expected["faces"] or not np.allclose(
            mesh.bounds, expected["bounds"], rtol=0, atol=config["signature_tolerance_mm"]
        ):
            raise FitError(
                f"{name}: bounds/face count differ from case glock-iwb-v1; "
                "do not apply these coordinates to another variant"
            )
    require_solid(original["carrier"], "carrier", single=True)
    require_solid(original["wing"], "wing", single=True)
    return original


def clip(mesh, lower, upper):
    return trimesh.boolean.intersection(
        [mesh, trimesh.creation.box(bounds=[lower, upper])], engine="manifold"
    )


def _bounds_covering(*meshes):
    # A margin beyond all inputs avoids unintentional truncation by a magic box.
    bounds = np.array([mesh.bounds for mesh in meshes])
    return bounds[:, 0].min(axis=0) - 10, bounds[:, 1].max(axis=0) + 10


def correct_geometry(carrier_aligned, wing_aligned, config):
    lower, upper = _bounds_covering(carrier_aligned, wing_aligned)
    seam = config["seam_y_aligned"]
    body_upper = upper.copy()
    body_upper[1] = seam
    hinge_lower = lower.copy()
    hinge_lower[1] = seam - config["graft_overlap"]
    body = clip(carrier_aligned, lower, body_upper)
    hinge = clip(wing_aligned, hinge_lower, upper)
    require_solid(body, "retained body")
    require_solid(hinge, "wing hinge")
    corrected = trimesh.boolean.union([body, hinge], engine="manifold")
    corrected.apply_translation(-np.array(config["carrier_translation"]))
    require_solid(corrected, "corrected carrier", single=True)
    coupon = clip(corrected, *config["coupon_bounds_original"])
    coupon.apply_transform(np.array(config["coupon_orientation"], dtype=float))
    require_solid(coupon, "hinge test", single=True)
    coupon.apply_translation(-coupon.bounds[0])
    return corrected, coupon


def validate(candidate_original, original, holster, config):
    facts = mesh_facts(candidate_original)
    require_solid(candidate_original, "candidate", single=True)
    tol = config["volume_tolerance_mm3"]
    lower, upper = _bounds_covering(candidate_original, original)
    upper[1] = config["body_guard_y_original"]
    a, b = [clip(m, lower, upper) for m in [original, candidate_original]]
    require_solid(a, "original guarded body")
    require_solid(b, "candidate guarded body")
    lost = trimesh.boolean.difference([a, b], engine="manifold")
    added = trimesh.boolean.difference([b, a], engine="manifold")
    body_difference = volume(lost) + volume(added)
    candidate = candidate_original.copy()
    candidate.apply_translation(config["carrier_translation"])
    intersections = []
    pin_intersections = {"carrier": [], "holster": []}
    z_lo, z_hi = config["pin_z_range"]
    pin = trimesh.creation.cylinder(radius=config["pin_radius"], height=z_hi - z_lo, sections=96)
    pin.apply_translation([*config["pin_axis"][:2], (z_hi + z_lo) / 2])
    for offset in config["axial_offsets_mm"]:
        shifted = candidate.copy()
        shifted.apply_translation([0, 0, offset])
        for angle in config["angles_deg"]:
            moved = shifted.copy()
            moved.apply_transform(
                trimesh.transformations.rotation_matrix(
                    np.radians(angle), [0, 0, 1], config["pin_axis"]
                )
            )
            inter = trimesh.boolean.intersection([holster, moved], engine="manifold")
            intersections.append(
                {"angle_deg": angle, "axial_offset_mm": offset, "intersection_mm3": volume(inter)}
            )
        # Rotation about the pin axis leaves this circular pin invariant.
        inter = trimesh.boolean.intersection([shifted, pin], engine="manifold")
        pin_intersections["carrier"].append(volume(inter))
    inter = trimesh.boolean.intersection([holster, pin], engine="manifold")
    pin_intersections["holster"].append(volume(inter))
    return {
        "checks": {
            "watertight": facts["watertight"],
            "consistent_winding": facts["consistent_winding"],
            "single_solid": facts["single_solid"],
            "positive_volume": bool(candidate_original.volume > 0),
            "body_preserved": body_difference < tol,
            "no_holster_interference_at_sampled_poses": all(
                r["intersection_mm3"] < tol for r in intersections
            ),
            "straight_1_75_mm_pin_clear": all(
                v < tol for values in pin_intersections.values() for v in values
            ),
        },
        "tolerance_mm3": tol,
        "body_guard_y_original_mm": config["body_guard_y_original"],
        "body_difference_mm3": body_difference,
        "intersections": intersections,
        "pin_intersections_mm3": pin_intersections,
        "mesh": facts,
    }
