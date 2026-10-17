# Reproduce the correction

## 1. Obtain the three input meshes

Get the original design from
[AuxArc on MakerWorld](https://makerworld.com/en/models/3422334-parametric-iwb-holster-for-glock-platform#profileId-3899917).
The source listing, model 3422334/profile 3899917, contains the G17/G19
holsters, normal wing, and magazine carrier. Supply the three STL variants
listed below. Preserve their original object coordinates: do not scale,
mirror, arrange, or reorient them before exporting. Renaming files is fine.

Create a local `inputs/` directory and place the files there:

```text
inputs/
  G17 Parametric Glock IWB RH With Bump.stl
  Holster Wing.stl
  IWB EDC Parametric Mag Carrier Glock.stl
```

These files are not included or downloaded by this project. A later designer
revision or another parametric variant may have different dimensions or
coordinates. The program rejects mismatching face counts or bounds. Those
checks are a coarse variant check, not a cryptographic identity test; matching
them does not prove two models have identical geometry.

The known signatures and coordinates are recorded in
[`cases/glock-iwb-v1.json`](../cases/glock-iwb-v1.json). Each run also records
SHA-256 hashes of the actual inputs, case file, and exported STLs.

## 2. Install the code and locked environment

Requires Python 3.12 or later and [uv](https://docs.astral.sh/uv/getting-started/installation/).
From a terminal:

```sh
git clone https://github.com/darron/auxarc.git
cd auxarc
uv sync --locked
```

This installs the exact resolved geometry and test dependencies in `uv.lock`.
The geometry versions used for the supplied print were NumPy 2.5.4,
trimesh 5.1.1, manifold3d 3.5.4, and NetworkX 3.7, on Python 3.12/macOS ARM64.

## 3. Build and validate

From the repository root, after putting the files in `inputs/`:

```sh
uv run --locked python -m auxarc build \
  --case cases/glock-iwb-v1.json \
  --carrier 'inputs/IWB EDC Parametric Mag Carrier Glock.stl' \
  --wing 'inputs/Holster Wing.stl' \
  --holster 'inputs/G17 Parametric Glock IWB RH With Bump.stl' \
  --output build/my-carrier-v1
```

Expected success begins with `PASS:`. Results appear only after the exported
STLs reload and pass validation. The command refuses an existing output
directory; choose a fresh output path for another run. Inputs are never
overwritten. Output publication reserves a new directory exclusively. An I/O
failure while copying validated results may leave a partial result directory;
the command then exits nonzero, and that directory is never silently reused.

Output files:

| File | Purpose |
|---|---|
| `Mag_Carrier_Corrected_Hinge_v1.stl` | Complete carrier, original carrier coordinates |
| `Carrier_Hinge_Fit_Test_v1.stl` | Small three-tooth test, oriented flat on bed |
| `original-validation.json` | Demonstrates the original collision |
| `corrected-validation.json` | Solid, collision, body-preservation, and pin checks |
| `manifest.json` | Input/output hashes, mesh facts, case hash, dependency and runtime versions |

All meshes and generated results stay local under ignored directories.
The case is specific; a failure is a reason to inspect the inputs, rather
than bypass a check or increase its tolerance to get `PASS`.

## 4. Saved aligned references and exact reproduction

The initial investigation saved aligned STL copies before the original
Desktop files became unavailable. Those saved copies were used to make the
revised print file. To reproduce from the same copies, supply:

```sh
uv run --locked python -m auxarc build \
  --case cases/glock-iwb-v1.json --frame aligned \
  --carrier inputs/carrier_aligned.stl \
  --wing inputs/wing_aligned.stl \
  --holster inputs/holster_reference.stl \
  --output build/from-aligned-references
```

`--frame aligned` means the carrier and wing have **already** undergone the
operations in [the technical details](technical-details.md). Do not use it for ordinary original STLs.
The holster is unchanged in either mode.

The reference hashes are published in [the evidence manifest](../evidence/reference-manifest.json).
With those exact local references and the recorded environment, this code
regenerated both originally supplied STLs byte-for-byte. The original-frame
path is also tested using inverse-transformed, STL-round-tripped references;
those reconstructed originals are not claimed to be byte-identical to the
now-unavailable original Desktop files. Fresh exports and other platforms may
triangulate differently: compare the validation results and geometric
difference, not just an STL byte hash.

## 5. Run tests

Public tests use synthetic meshes; they do not need or download the models:

```sh
uv run --locked pytest -q
uv run --locked ruff check .
uv run --locked ruff format --check .
```

Without local reference meshes, the five integration tests explicitly skip.
To include them:

```sh
AUXARC_REFERENCE_DIR='/path/to/saved/aligned/references' \
AUXARC_PRINTED_STL='/path/to/Mag_Carrier_Corrected_Hinge_v1.stl' \
uv run --locked pytest -q
```

The reference directory must contain `carrier_aligned.stl`, `wing_aligned.stl`,
and `holster_reference.stl`. `AUXARC_PRINTED_STL` points to the previously
supplied print file, not a newly generated candidate. This enables a geometric
comparison against that file. It does not establish full physical pin passage.
The separate historical byte-comparison test explicitly skips if the runtime
or dependency versions differ from the recorded manifest; geometric/report
comparisons still run with local reference meshes.
