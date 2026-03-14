# Portal Data Models

Unified, standards-compliant data models for phenotypes and other entities used across the [A2F Knowledge Portal](https://a2f.hugeamp.org/) and related Flannick Lab resources.

## What's in here

Each phenotype in the portal gets:

- A **stable numeric ID** (`PORTAL:0000001` through `PORTAL:0006982`)
- A **trait type classification** (disease, measurement, interaction, stratified, adjusted, etc.)
- **Cross-ontology mappings** to EFO, MESH, MONDO, HP, DOID, ORPHANET, CHEBI, OBA, and CMO
- A **SKOS predicate** for each mapping (`exactMatch`, `broadMatch`, `closeMatch`, `narrowMatch`, `relatedMatch`)
- A **confidence score** and **provenance** for every mapping

Output is a [LinkML](https://linkml.io/) schema with data conforming to the [SSSOM](https://mapping-commons.github.io/sssom/) specification.

## Quick start

```bash
# Install dependencies
uv sync

# Generate v0.0.1 from source files (~5 min first run)
./scripts/phenotype/generate.sh

# Fast rebuild (skip OWL parsing, uses cached cross-references)
./scripts/phenotype/generate.sh --skip-owl

# Fast rebuild (skip OWL parsing AND OLS/OMIM API calls)
./scripts/phenotype/generate.sh --skip-owl --skip-api
```

Output lands in `versions/phenotype/v0.0.1/`.

## Repository structure

```
portal-data-models/
├── schemas/phenotype/
│   └── portal_phenotype.yaml          # LinkML schema definition
│
├── scripts/phenotype/
│   ├── generate.sh                    # Single entry point for the full pipeline
│   ├── 01_parse_sources.py            # Parse raw source files
│   ├── 02_parse_efo_xrefs.py          # Extract cross-references from EFO/ORDO OWL
│   ├── 03_enrich.py                   # OLS API + GWAS Catalog + xref expansion + labels + validation
│   ├── 04_generate_output.py          # Assign PORTAL IDs, write versioned SSSOM + YAML
│   ├── 05_quality_report.py           # Generate coverage report
│   ├── 09_export_review_table.py      # (optional) Export TSV for manual review
│   └── 10_apply_review.py             # (optional) Apply manual review flags
│
├── raw/phenotype/                     # Source data (read-only, do not modify)
│   ├── Phenotypes.tsv                 # 6,982 phenotypes (master registry)
│   ├── portal_to_mesh_curated_collected.tsv
│   ├── amp-traits-mapping-portal-phenotypes_06262024.csv
│   ├── gcat_v1.0.3.1.tsv             # GWAS Catalog studies
│   ├── efo.owl                        # EFO ontology (330 MB)
│   └── ORDO_en_4.5.owl               # Orphanet ontology (45 MB)
│
├── data/phenotype/                    # Intermediate files (gitignored, regenerated)
│
├── versions/phenotype/                # Versioned output (checked into git)
│   └── v0.0.1/
│       ├── portal_phenotypes.yaml              # Full phenotype collection (LinkML)
│       ├── portal_phenotype_mappings.sssom.tsv  # SSSOM mapping set
│       ├── portal_phenotype_registry.tsv        # ID registry
│       └── mapping_coverage.md                  # Quality report
│
├── .env                               # OMIM API key (optional, gitignored)
└── pyproject.toml
```

## Output files

Each version contains three main files:

### `portal_phenotypes.yaml`

The complete phenotype collection as LinkML instance data. Each entry includes the PORTAL ID, legacy ID, trait type, and all cross-ontology mappings with labels, predicates, confidence, and provenance.

### `portal_phenotype_mappings.sssom.tsv`

Standard [SSSOM](https://mapping-commons.github.io/sssom/) mapping set. Each row maps a PORTAL ID to an external ontology term with a SKOS predicate and confidence score. Can be consumed by any SSSOM-compatible tool.

### `portal_phenotype_registry.tsv`

Simple flat registry mapping PORTAL IDs to legacy IDs, phenotype names, display groups, and trait types.

## Pipeline overview

The `generate.sh` script runs five steps in order:

| Step | Script | What it does | Time |
|------|--------|-------------|------|
| 1 | `01_parse_sources.py` | Parse Phenotypes.tsv, MeSH mappings, AMP/EFO mappings, GWAS Catalog, Orphanet IDs | ~5s |
| 2 | `02_parse_efo_xrefs.py` | Extract cross-references from EFO and ORDO OWL files | ~75s |
| 3 | `03_enrich.py` | Xref expansion, OLS API search, GWAS Catalog MAPPED_TRAIT matching, broad EFO assignment, label backfill, validation fixes | ~4 min |
| 4 | `04_generate_output.py` | Assign PORTAL IDs, generate versioned SSSOM + YAML + registry | ~5s |
| 5 | `05_quality_report.py` | Generate mapping coverage report | ~2s |

Step 2 can be skipped on subsequent runs with `--skip-owl` (uses the cached cross-reference table). Step 3's API calls can be skipped with `--skip-api` for fast iteration.

## Versioning

Versions live in `versions/phenotype/v{MAJOR}.{MINOR}.{PATCH}/`.

- **v0.0.1** is the base version generated entirely from the source files by the automated pipeline. It should always be reproducible by running `generate.sh` from scratch.
- Subsequent versions (v0.0.2, v0.1.0, etc.) incorporate manual curation, corrections, or new source data.

To create a new version:

```bash
# Generate from the current enriched data with a new version number
uv run python scripts/phenotype/04_generate_output.py --version 0.0.2
uv run python scripts/phenotype/05_quality_report.py --version 0.0.2
```

## v0.0.1 coverage

| Metric | Value |
|--------|-------|
| Total phenotypes | 6,982 |
| Total mappings | 21,081 |
| Mapping coverage | 100% |
| Label coverage | 85% |

| Target | Result |
|--------|--------|
| >90% portal phenotypes mapped to EFO/MONDO/MESH | 100% |
| >95% rare disease phenotypes mapped to ORPHANET | 100% |
| >80% GWAS Catalog traits mapped to EFO | 100% |

## Manual review workflow

If you want to review and correct mappings by hand:

```bash
# 1. Export a review spreadsheet
uv run python scripts/phenotype/09_export_review_table.py

# 2. Open data/phenotype/review_mappings.tsv in Excel/Google Sheets
#    Fill the "flag" column: remove, broad, narrow, close, related, exact
#    Save the file

# 3. Apply your flags
uv run python scripts/phenotype/10_apply_review.py

# 4. Generate a new version with your corrections
uv run python scripts/phenotype/04_generate_output.py --version 0.0.2
uv run python scripts/phenotype/05_quality_report.py --version 0.0.2
```

## Contributing

1. **Found a bad mapping?** Open an issue describing the phenotype, the incorrect mapping, and what the correct mapping should be.

2. **Want to fix mappings?** Fork the repo, use the manual review workflow above to make corrections, generate a new version, and open a pull request. Include the version diff in your PR description.

3. **Adding new source data?** Place new source files in `raw/phenotype/`, update the parsing logic in `01_parse_sources.py`, and regenerate. Bump the version.

4. **Adding a new data model?** Create new subdirectories under `schemas/`, `scripts/`, `raw/`, and `versions/` (e.g., `schemas/variant/`, `scripts/variant/`). Follow the same pattern as the phenotype model.

### PR checklist

- [ ] New version directory in `versions/phenotype/v{X.Y.Z}/` with all output files
- [ ] Quality report shows all targets passing
- [ ] No `MESH:none` or other invalid target IDs in output
- [ ] All ontology prefixes are uppercase (MESH, ORPHANET, not MeSH, Orphanet)

## Git LFS

Large source files (OWL ontologies, GWAS Catalog TSVs) are stored with [Git LFS](https://git-lfs.github.com/). You need it installed to clone and work with this repo.

```bash
# Install git-lfs (macOS)
brew install git-lfs

# After cloning, pull LFS files
git lfs install
git lfs pull
```

If you cloned without LFS, the large files will be pointer stubs. Run `git lfs pull` to download the actual content.

Tracked patterns (see `.gitattributes`):
- `raw/**/*.owl` — EFO (330 MB), ORDO (45 MB)
- `raw/**/*.tsv` — GWAS Catalog (59 MB, 30 MB), Phenotypes, MeSH mappings

## Dependencies

Defined in `pyproject.toml`. Install with `uv sync`.

- **linkml** / **linkml-runtime** — schema definition and validation
- **sssom** — SSSOM format support
- **rdflib** — OWL/RDF parsing
- **pandas** — tabular data processing
- **aiohttp** — async HTTP for OLS API
- **python-dotenv** — `.env` file loading (for optional OMIM API key)

## Optional: OMIM labels

To include OMIM disease labels in the output, create a `.env` file at the repo root:

```
OMIM_API_KEY=your_key_here
```

Get a key at [omim.org/api](https://omim.org/api). Without it, OMIM mappings will still be included but without human-readable labels.
