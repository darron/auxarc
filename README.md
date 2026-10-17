# AuxArc carrier hinge fit study

An independent explanation and reproducible correction for one combination of
AuxArc's IWB holster, working wing, and magazine-carrier STL files.

**Result so far:** the revised carrier seats in the user's printed holster.
Full-length passage of the PETG filament pin remains **unconfirmed**: it is
tight, and the user does not want to force it. Using the private saved aligned
reference meshes, the code reproduces the previously supplied revised STL
byte-for-byte on the recorded environment.
That proves reproduction of the file; it does not prove complete assembly.

Original design: [AuxArc's Parametric IWB Holster for Glock Platform](https://makerworld.com/en/models/3422334-parametric-iwb-holster-for-glock-platform#profileId-3899917).
This is not the designer's official repository.

## What was happening

The filament could pass through the holster by itself, through the carrier by
itself, and through the holster assembled with the normal wing. It would not
enter the first carrier knuckle when the original carrier was interleaved.

The supplied files show matching 20 mm tooth spacing and matching nominal
2.2 mm bores. However, when their pin axes are aligned, the original carrier's
material at the bottoms of its gaps overlaps the holster knuckles. At the
documented flat assembly position, that overlap is approximately **28.69 mm³**.
This provides a geometric explanation for why individually clear holes can
be difficult to align during assembly. It does not rule out support residue
or printing tolerances contributing to the physical tightness.

## What changed

The normal wing already worked. Its hinge and adjacent neck were used as a
reference, then joined to the existing carrier body. The carrier was not
scaled globally.

| Feature | Original carrier | Revised hinge |
|---|---:|---:|
| Tooth width along pin | 9.8 mm | 9.6 mm |
| Tooth spacing | 20 mm | 20 mm |
| Approximate knuckle diameter | 7.9 mm | 7.5 mm |
| Nominal pin bore | 2.2 mm | 2.2 mm |
| Roots between teeth | Interfere in aligned flat pose | Working wing profile |

The receiver gaps are 10 mm wide: centered side clearance increases from
0.1 to 0.2 mm per side. The retained carrier body, including its cavity and
mounting features at least 0.5418 mm behind the hinge seam, is checked for
added or removed volume. The front hinge is checked against the donor, and
a small three-tooth test piece is checked against its intended cut.

## Start here

- **For a CAD modeler:** [The measurements and equivalent modeling steps](docs/method.md).
  This explains the change without requiring Python or Git knowledge.
- **To run the code:** [Download, setup, inputs, and reproduction commands](docs/reproduce.md).
- **To assess the evidence:** [What was checked and what remains uncertain](docs/validation.md).
- **Independent review:** [Claude and Amp/Oracle findings and resolutions](docs/review.md).
- **Before sharing meshes:** [Attribution and the source model's license](NOTICE.md).

The repository includes code, case coordinates, tests, dependency locks, and
numerical evidence. Source and modified STL files are deliberately absent:
the original listing's license restricts their redistribution. Supply your
own copies locally. This is a measured correction for the identified files,
not an automatic repair for every parameter combination or later revision.
