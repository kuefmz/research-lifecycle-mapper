# Executed verification

Historical measurements/audit: retain the source version and denominators below. For current jointly adjudicated documentation reference status and source/code interpretation, see [2026-10-20 annotation status](annotation_status_20261020.md). No historical scores have been relabeled as new measurements.

The implementation and committed synthetic reference were verified in Python 3.12.14 with uv 0.12.23 and frozen dependencies.

Executed successfully:

* `uv sync --frozen` — development environment installation.
* `ruff check src tests scripts` — all checks passed.
* `ruff format --check src tests scripts` — formatting verified.
* `mypy` — no issues in nine source modules.
* `pytest -q --basetemp local/pytest` — 59 tests passed.
* `uv build --wheel` — built a wheel containing all six packaged rule catalogs.
* Installed that wheel with `--no-deps` into a separate environment; isolated `python -I -m lifecycle_mapper analyze` successfully loaded the packaged rules and returned all six expected labels for the documentation-positive synthetic snapshot.
* Generated `benchmark/results/synthetic-v1` from a clean checkout of implementation commit `6a1d8575b542938eab7da0c2338e03713ced31e7`; its manifest records that commit, rule/input hashes, runtime, source hash and lockfile hash.
* Ran `benchmark verify` with two new runs and the committed synthetic reference. Every current canonical artifact was byte-identical between reruns. All semantic reference artifacts matched; original reference producing-manifest metadata was preserved.

The five synthetic repositories cover documentation positives, implementation positives, generic engineering negatives, excluded/future/test evidence and one incomplete acquisition. The fixture's reported scores are software regression expectations, not estimates of human benchmark performance.

No human benchmark evaluation, full live repository acquisition, Docker build or anonymous publication was executed here. Live acquisition is tested through a mocked GitHub API. Remote GitHub Actions status should be inspected on the pull request; it is not substituted for the local results above.

Run the README's verification commands in a fresh checkout and use new output directories. The baseline reference's classifier commit remains the original producing implementation commit even after documentation/reference-result commits are added.

## v0.2.0 verification scope

The v0.1 reference and results above are historical. The current revision adds Agreement Final import, structured documentation matching and split/freeze controls. Its current test count and producing source commit are recorded in verification_v2.md. Synthetic-v1 outputs remain unchanged for provenance; current CI compares synthetic-v2. No human performance results have been generated.
