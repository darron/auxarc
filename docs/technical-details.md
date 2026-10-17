# Explanation for the original designer or another CAD modeler

## Scope and observations

This study concerns three STL files from AuxArc's
[Parametric IWB Holster for Glock Platform](https://makerworld.com/en/models/3422334-parametric-iwb-holster-for-glock-platform#profileId-3899917):

1. `G17 Parametric Glock IWB RH With Bump.stl`
2. `Holster Wing.stl`
3. `IWB EDC Parametric Mag Carrier Glock.stl`

The user could thread PETG filament through each component separately. The
normal wing assembled successfully. The original carrier would not accept
the filament into its first knuckle while interleaved with the holster.

**Current physical status:** the revision seats and interleaves with the holster.
The filament reaches and starts entering the last hinge section, but remains
tight. Full-length pin passage is unconfirmed. Reproducing the digital file
byte-for-byte does not establish complete physical assembly.

The working wing is the useful control here. This report concerns the
supplied meshes and their measured fit, rather than the quality of the
designer's modeling work or the behavior of every parametric version.

All dimensions below are interpreted as millimeters. STL files do not
themselves declare a length unit.

## Matching pitch and bores, different clearance

The three carrier teeth are 9.8 mm wide, at 20 mm pitch. The working wing's
teeth are approximately 9.6 mm wide at the same pitch. The holster has 10 mm
receiving gaps. Centered clearance per side is therefore:

- Original carrier: `(10 - 9.8) / 2 = 0.1 mm`.
- Working wing: `(10 - 9.6) / 2 = 0.2 mm`.

Nominal pin bores measure 2.2 mm in all three supplied models. The outside
diameter of the carrier's hinge knuckles is approximately 7.9 mm; the working
wing's is approximately 7.5 mm. Thus the carrier is tighter both axially and
around the knuckles. Narrower teeth alone do not address the root collision.

## The important collision is at the gap roots

Here, "assembled" coordinates mean the holster's original coordinates, with
the wing and carrier rigidly aligned to its pin axis. The exact operations
are given below; no part is scaled to make these comparisons.

With the pin axes coincident and teeth centered in the holster's gaps, the
original carrier overlaps the holster by approximately 28.69258 mm³ in the
flat/outward pose. The main overlap is where a holster knuckle meets the
carrier material at the bottom of a gap between carrier teeth.

A cross-section through a holster knuckle at assembled Z=32 mm found:

- Holster's flat lower boundary: Y=-14.684 mm.
- Working wing's flat gap root: Y=-15.3107 mm, leaving about 0.627 mm clearance.
- The original carrier's curved root reaches approximately Y=-13.9463 mm,
  overlapping that boundary by up to about 0.738 mm at this section.

The original investigation checked both 3D solid intersection and an
independent 2D cross-section intersection. These measurements explain a
potential assembly obstruction. They are not physical measurements of the
printed parts. Rotating the original carrier reduces the overlap but did
not eliminate it at the sampled favorable angles.

## Equivalent change in a CAD editor

1. Keep the magazine pocket and mounting geometry at their existing size.
2. Align the working wing's and carrier's pin axes. Center the teeth in the
   holster gaps; preserve the 20 mm pitch and existing axial placement.
3. Use the working wing's complete three-tooth hinge and adjacent neck as
   the replacement profile: approximately 9.6 mm tooth widths, 7.5 mm
   knuckle diameter, and 2.2 mm bores. Copy the root clearance as well.
4. Retain the carrier body behind a plane 4.5767 mm from the pin centerline
   toward the carrier body. In the assembled coordinate system used here,
   this is Y=-15.3107 mm; the pin centerline is Y=-10.734 mm.
5. Extend the donor neck 0.5 mm behind that joining plane, into the retained
   body, and Boolean-union them. The overlap makes a connected joint;
   merely making two surfaces touch would be less reliable.
6. Check for one closed solid, aligned bores, preserved carrier body, and
   clearance against the actual holster. Print a small hinge test before
   committing to another complete carrier.

For the designer's original coordinate frames: the carrier cut is at
Y=-28.3582 mm and the donor neck reaches Y=-28.8582 mm. In the wing's original
frame, the seam is Y=8.3062 mm and the donor selection is Y<=8.8062 mm.
The script's positive rotations follow the right-hand rule about assembled
+Z (counterclockwise when viewed from +Z toward the origin). The 0–90° samples
check the outward-opening side established by the working wing's alignment;
they do not certify other angles, mirrored versions, or a continuous path.

These CAD steps have improved the observed seating. The final physical
pin-through test remains incomplete.

This is a local hinge replacement. Enlarging the bore or scaling the whole
carrier would change different features and would not reproduce this fix.

## Exact coordinate operations used by the code

The holster defines the common assembly frame. Its pin axis runs along Z,
through X=12.385 mm, Y=-10.734 mm.

Carrier original coordinates become assembly coordinates by translation:

```text
X_assembled = X_carrier + 2.161
Y_assembled = Y_carrier + 13.0475
Z_assembled = Z_carrier + 2.8961
```

The wing's hinge originally runs along X. This rigid rotation and translation
places it along the holster's Z axis:

```text
X_assembled =  Z_wing + 8.635
Y_assembled = -Y_wing - 7.0045
Z_assembled =  X_wing + 16.70265
```

Neither operation scales or mirrors the models. The correction is:

```text
retained body = carrier intersect {Y <= -15.3107}
donor hinge   = wing    intersect {Y >= -15.8107}
revised part  = union(retained body, donor hinge)
```

The result is translated back into the carrier's original coordinate system
before STL export. Constants are in [the case JSON](../cases/glock-iwb-v1.json).

The test piece retains the revised part within original-coordinate bounds
X=6.474..100, Y=-36..100, Z=13..65.5 mm. The deliberately large upper bounds
serve as clipping limits rather than claimed part dimensions. It preserves
all three knuckles, crops the supporting plate, and trims about 0.1954 mm
from that plate's underside to give a common flat print bed with the hinge.
Only the test piece receives this trim. It is rotated to
`(new X,new Y,new Z)=(old Z,-old Y,old X)` and shifted to nonnegative coordinates.
