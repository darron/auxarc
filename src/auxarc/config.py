"""Validate numerical assumptions before doing geometry or writing outputs."""

import numpy as np

from .carrier import FitError


def validate_config(config):
    try:
        if config["schema_version"] != 1 or config["units"] != "mm":
            raise ValueError("expected schema 1 and mm units")
        signatures = config["source_signatures_original"]
        if not isinstance(signatures, dict) or set(signatures) != {"carrier", "wing", "holster"}:
            raise ValueError("source signatures must include carrier, wing, and holster")
        for name, signature in signatures.items():
            faces = signature["faces"]
            bounds = np.asarray(signature["bounds"], dtype=float)
            if (
                type(faces) is not int
                or faces <= 0
                or bounds.shape != (2, 3)
                or not np.isfinite(bounds).all()
                or not (bounds[1] > bounds[0]).all()
            ):
                raise ValueError(f"invalid source signature for {name}")
        for key, shape in [
            ("carrier_translation", (3,)),
            ("pin_axis", (3,)),
            ("coupon_bounds_original", (2, 3)),
            ("pin_z_range", (2,)),
        ]:
            a = np.asarray(config[key], dtype=float)
            if a.shape != shape or not np.isfinite(a).all():
                raise ValueError(f"{key} must be finite with shape {shape}")
        for key in ["wing_transform", "coupon_orientation"]:
            a = np.asarray(config[key], dtype=float)
            if a.shape != (4, 4) or not np.isfinite(a).all():
                raise ValueError(f"{key} must be a finite 4x4 rigid transform")
            r = a[:3, :3]
            if (
                not np.allclose(r.T @ r, np.eye(3))
                or not np.isclose(np.linalg.det(r), 1)
                or not np.allclose(a[3], [0, 0, 0, 1])
            ):
                raise ValueError(f"{key} must not scale, reflect, or shear the model")
        for key in ["angles_deg", "axial_offsets_mm"]:
            a = np.asarray(config[key], dtype=float)
            if a.ndim != 1 or not len(a) or not np.isfinite(a).all():
                raise ValueError(f"{key} must be nonempty and finite")
        for key in [
            "graft_overlap",
            "volume_tolerance_mm3",
            "signature_tolerance_mm",
            "pin_radius",
        ]:
            if not np.isfinite(config[key]) or config[key] <= 0:
                raise ValueError(f"{key} must be positive and finite")
        for key in ["seam_y_aligned", "body_guard_y_original"]:
            if not np.isfinite(config[key]):
                raise ValueError(f"{key} must be finite")
        donor_end = (
            config["seam_y_aligned"] - config["carrier_translation"][1] - config["graft_overlap"]
        )
        if not donor_end - 1 < config["body_guard_y_original"] < donor_end:
            raise ValueError("body guard must lie within 1 mm behind the donor overlap")
        if config["pin_z_range"][1] <= config["pin_z_range"][0]:
            raise ValueError("pin_z_range must increase")
        bounds = np.array(config["coupon_bounds_original"])
        if not (bounds[1] > bounds[0]).all():
            raise ValueError("coupon bounds must enclose positive volume")
    except (KeyError, TypeError, ValueError) as exc:
        raise FitError(f"Invalid case: {exc}") from exc
