# Independent review and verification

Reviewed on 2026-10-17 before first public publication. Scope: the complete
new repository against an empty upstream, including code, case coordinates,
numerical evidence, documentation, tests, and untracked publication files.
There were no pre-existing user edits in this new checkout.

## Reviewers and result

Claude Code reviewed the actual checkout and then performed a focused
confirmation after fixes. Amp also reviewed the checkout, obtained an Oracle
adversarial second opinion, and performed a focused confirmation. Amp reported
independently reproducing Oracle's missing-material validation counterexample.
Neither reviewer edited, committed, or published files.

Both final confirmations found no unresolved publication blocker. Their
recommendations were explicitly conditional on documenting the incomplete
physical result and committing the complete reviewed working tree.

Claude's first pass could inspect files, but its restricted shell allowlist
prevented test execution. That limitation was corrected for confirmation:
both Claude and Amp independently ran the public suite (then 31 passed,
4 skipped), Ruff lint/format checks, and checked the current case hash.
Amp also ran `git diff --check`. The final bookkeeping change split the
historical byte check into a separately reported test: public results are
now **31 passed, 5 skipped**, with all **36 passing locally** using private
references on the recorded runtime.

The reviewers did **not** independently reproduce the real-model geometry or
historical STL bytes: the licensed meshes were deliberately unavailable to
them. Those results are the local verification recorded in this repository.
Raw review transcripts remain outside the publication set.

## Accepted findings and fixes

| Finding | Resolution |
|---|---|
| Standalone CAD guide could be mistaken for complete physical success | State seating improved, filament starts into the last section, full passage remains unconfirmed |
| Tests did not protect both historical output hashes and published reports | Check source/case hashes, both output hashes on the recorded runtime, mesh facts, reports, and coordinate-mode geometric equivalence |
| An output-hash assertion could silently be omitted on another runtime | Separate byte-comparison test explicitly reports a skip when runtime/dependencies differ |
| No positive-material check for the replacement hinge | Compare donor front material by two-way Boolean difference; regression deletes hinge material |
| Coupon could be truncated while remaining one solid | Compare exported coupon against the intended cut and orientation; truncation regression |
| Input/case files could change between parsing and hashing | Parse and hash the same byte snapshots; concurrent-modification regression |
| Empty or incomplete source signatures could disable variant rejection | Require all three signatures, positive integer face counts, finite ordered bounds |
| POSIX directory rename could replace an existing empty directory | Reserve output directory exclusively and create files exclusively; no-overwrite regression |
| Body guard could be moved far behind the actual graft | Constrain it near the donor overlap; describe its exact preservation region |
| Coordinate conventions and publication/runtime boundaries needed detail | Add original-frame seam coordinates, rotation convention, runtime record, Python version, and tracked-asset checks |

A separate self-audit extended the ideal-pin check from assembled Z=6..88 mm
to Z=6..103 mm to include the final holster hinge section. A regression covers
an obstruction in that section. The case hash and evidence were regenerated.
**Neither generated STL changed.**

## Deliberately unresolved or deferred

- Full physical pin passage and complete assembly remain unconfirmed.
- Sampled ideal-model checks do not establish strength, durability, print
  tolerances, or an unobstructed continuous assembly path.
- A diagnostic search for the largest ideal pin radius was deferred. It is
  unnecessary to reproduce the documented change and would not measure the
  printed bore or explain its remaining tightness.
- A disk error during publication can leave a partial output directory. The
  command exits nonzero and never silently reuses or overwrites that directory.

Final local gates: 36 tests passed with private references; public suite
31 passed/5 explicitly skipped; Ruff lint and format, package build, local
documentation links, and `git diff --check` passed. Both regenerated STL files
were also directly compared byte-for-byte to the earlier supplied outputs.
GitHub's public Linux/macOS checks run only the public suite; consult the
repository's Actions results for the current commit.
