# Evidence and limits

## Physical observation, 2026-10-17

The user reported that the revised carrier fits into the holster. A later
photo shows interleaved printed knuckles. The user then clarified that the
PETG filament is tight and they are unsure it has passed all the way through.

Therefore the physical result is **improved seating/interleaving, with
full-length pin passage unconfirmed**. The record does not establish an
unobstructed full pin, measured insertion force, durability, strength,
retention, or performance across temperatures and repeated cycles.

The photo was examined locally. No original photo or its metadata is included
in this public repository. There are no photos in the publication set.

## Numerical checks on the supplied meshes

| Check | Original carrier | Revised carrier |
|---|---|---|
| Closed solid, consistent winding, positive volume | Pass | Pass |
| Interference at flat pose, centered teeth | About 28.69258 mm³ | 0 mm³ reported by Boolean engine |
| Seven angles, two axial mounting positions | Collision at sampled poses | No intersection above tolerance |
| Straight 1.75 mm pin, ideal coincident axes | Clear | Clear |
| Retained body comparison | Self-comparison | No added or removed volume reported |

Angles tested are 0°, 15°, 30°, 45°, 60°, 75°, and 90° about the hinge axis.
Axial positions differ by 20 mm. These are **14 static poses**, not a continuous
motion sweep or proof of an unobstructed insertion path. Original interference
persists at sampled favorable angles, even though it becomes much smaller.

The pin check uses a 96-sided cylinder of radius 0.875 mm over assembled
Z=6..88 mm. This avoids the holster's closed lower end, which is not part of
the pin channel. It checks both carrier axial positions. An ideal pin clearing
each aligned model does not mean their colliding original solids can actually
occupy that alignment. Nor does it measure printing errors in a 2.2 mm bore.

Body preservation compares both directions of Boolean difference for material
behind original carrier Y=-28.9 mm. This lies beyond the replacement seam
Y=-28.3582 mm and the donor's 0.5 mm overlap. The gap between the comparison
plane and graft cut avoids coincident-plane numerical artifacts. This is an
explicit region check, not a claim that the hinge itself was preserved.

All collision/difference pass thresholds are **0.0001 mm³**. This numerical
threshold is neither a manufacturing tolerance nor a clearance guarantee.
The exported files are reloaded before validation; each must remain one
watertight solid. The original holster reference has a main solid and a tiny
closed artifact; both are retained in collision checks.

## Reproduction of the supplied print file

The packaged workflow regenerated both earlier output STLs **byte-for-byte**
using the saved aligned reference files and the recorded dependency versions.
This is stronger evidence of file reproduction than an approximate volume
comparison. It does not strengthen the physical fit claim beyond the observed
seating described above.

The full-carrier file SHA-256 is:

```text
1e48cc4ef382ea8fc57f00715b093237323f28512b49b6d964b6be38f2e2bd0a
```

The hinge test file SHA-256 is:

```text
920c299c4855d5f5481667f6d27d78a17f320d5b3e5a759c3277b95038979269
```

The numerical reports and input/output hashes are in [evidence/](../evidence/).
They are historical results, not results fabricated by public CI. The source
meshes remain local because their license restricts redistribution.

## Test coverage

Synthetic tests exercise clipping against independently calculated volumes,
rigid alignment, the graft's changed and retained regions, invalid meshes,
body loss, pin obstruction, solid collision, malformed case data, missing
inputs, and wrong variants. Local integration tests exercise the full CLI,
both coordinate modes, refusal to overwrite results, and comparison against
the originally supplied full-carrier STL.

GitHub CI runs the public synthetic suite on Linux and macOS. It explicitly
does not run the source-model integration tests, because it has no licensed
source models. A green public check is not independent confirmation of the
specific model's fit. Local full-model results are reported separately.
